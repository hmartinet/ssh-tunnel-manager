#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK

import os
import appdirs
import yaml
import subprocess
import argparse
import argcomplete
from shutil import copyfile
from ssh_tunnel_manager.version import __version__

APP_NAME = "SSH Tunnel Manager"
APP_AUTHOR = "Hervé Martinet"
APP_VERSION = __version__

STM = 'stm'
CONF_FILE = 'config.yml'
CONF_DEFAULT_FILE = 'conf/default_config.yml'
DNSMASQ_DIR = '/etc/NetworkManager/dnsmasq.d'
DNSMASQ_FILE = 'dnsmasq-stm.conf'
DNSMASQ_DEFAULT_FILE = 'dnsmasq-stm.conf'


class Controller(object):

    def __init__(self):
        self._dir = os.path.dirname(os.path.realpath(__file__))
        conf_dir = os.path.dirname(
            appdirs.user_data_dir(APP_NAME, APP_AUTHOR, version=APP_VERSION))
        if not os.path.exists(conf_dir):
            os.makedirs(conf_dir)
        self.conf_file = '{}/{}'.format(conf_dir, CONF_FILE)
        if not os.path.exists(self.conf_file):
            copyfile('{}/{}'.format(
                self._dir, CONF_DEFAULT_FILE), self.conf_file)
        with open(self.conf_file, 'r') as f:
            self.conf = Config(yaml.load(f))
        self.parse_args()

    def parse_args(self):
        self.parser = argparse.ArgumentParser()

        self.parser.add_argument(
            '-v', '--version', action='store_true', dest='version',
            help="display current version")
        self.parser.add_argument(
            '-c', '--config', action='store_true', dest='config',
            help="edit configuration file")
        self.parser.add_argument(
            '--set-editor', dest='editor', metavar="nano|vim|gedit|...",
            help="set editor for config file")
        self.parser.add_argument(
            '--auto-conf-network-manager', action='store_true',
            dest='auto_stm', help="auto configure Network-Manager dnsmasq "
            "with .stm domain")

        def hop_arg(parser):
            default_hop = self.conf.get('ssh', 'default-hop')
            parser.add_argument(
                '-H', '--hop', dest='hop', nargs='?',
                const=default_hop, default=None,
                help="use a hop server, default {}".format(default_hop))

        def hop_port_arg(parser):
            parser.add_argument(
                '-P', '--hop-port', dest='hop_port',
                help="use a custom port for hop server, "
                "default same as local port")

        server_parsers = self.parser.add_subparsers(
            metavar="SERVER", dest='server')
        for srv, srv_conf in self.conf.items('servers'):
            parser_server = server_parsers.add_parser(
                srv, help=srv_conf.get('help', default=srv_conf.get('ip')))
            hop_arg(parser_server)
            command_parsers = parser_server.add_subparsers(
                metavar="COMMAND", dest='command')
            for cmd, cmd_conf in srv_conf.items('tunnels'):
                parser_command = command_parsers.add_parser(
                    cmd, help=cmd_conf.get('help', default=cmd))
                parser_command.add_argument(
                    '-p', '--port', dest='port',
                    help="override local port")
                hop_arg(parser_command)
                hop_port_arg(parser_command)

        argcomplete.autocomplete(self.parser)
        self.args = self.parser.parse_args()

    def run(self):
        if self.args.version:
            print('{}{}{} {}'.format(
                Bash.Style.BOLD, APP_NAME, Bash.Style.ENDC, APP_VERSION))
            print
        elif self.args.auto_stm:
            if os.getuid() != 0:
                Bash.err(
                    "You need root rights to do that "
                    "(use 'sudo stm --auto-conf-network-manager')")
                return
            if not os.path.exists(DNSMASQ_DIR):
                Bash.err("folder {} does not exists".format(DNSMASQ_DIR))
                return
            Bash.head(
                Bash.Tag.FILE,
                '{}/{}'.format(DNSMASQ_DIR, DNSMASQ_FILE))
            copyfile('{}/{}'.format(self._dir, DNSMASQ_DEFAULT_FILE),
                     '{}/{}'.format(DNSMASQ_DIR, DNSMASQ_FILE))
            Bash.head(Bash.Tag.RUN, "service network-manager restart")
            subprocess.run(['service', 'network-manager', 'restart'])
            Bash.ok("Configuration updated")
        elif self.args.editor:
            subprocess.run([
                'sed', '-i',
                's/editor\s*:.*$/editor: {}/'.format(self.args.editor),
                self.conf_file])
        elif self.args.config:
            subprocess.Popen([self.conf.get('editor'), self.conf_file])
        elif self.args.server:
            server = self.conf.sub('servers', self.args.server)
            if self.args.command:
                command = server.sub('tunnels', self.args.command)
                local_port = self.args.port or command.get('local')
                self.print_tunnel(server, command)
                if self.args.hop:
                    self.connect(self.conf.get('ssh', 'hop-tunnel-cmd').format(
                        remote=server.get('ip'),
                        lport=local_port,
                        rport=command.get('remote'),
                        hop=self.args.hop,
                        hport=self.args.hop_port or local_port))
                else:
                    self.connect(self.conf.get('ssh', 'tunnel-cmd').format(
                        remote=server.get('ip'),
                        lport=local_port,
                        rport=command.get('remote')))
            elif self.args.hop:
                self.connect(self.conf.get('ssh', 'hop-cmd').format(
                    remote=server.get('ip'),
                    hop=self.args.hop))
            else:
                self.connect(self.conf.get('ssh', 'cmd').format(
                    remote=server.get('ip')))
        else:
            self.parser.print_help()

    def print_tunnel(self, server, command):
        local_port = self.args.port or command.get('local')
        hop_port = self.args.hop_port or local_port
        msg = "# {}:{} forwarding on {}.{}:{}{}...".format(
            server.get('ip'), command.get('remote'),
            self.args.server, STM, local_port,
            self.args.hop and ' (through {}:{})'.format(
                self.args.hop, hop_port) or '')
        print(Bash.Style.WARNING + Bash.Style.BOLD + msg + Bash.Style.ENDC)

    def connect(self, cmd):
        Bash.head(Bash.Tag.RUN, cmd)
        subprocess.run(cmd.split(' '))


class Config():

    def __init__(self, config):
        self.c = config

    def get(self, *path, default=None, node=None):
        def val(v):
            return default if v is None else v

        node = node or self.c
        if len(path) == 1:
            return val(node.get(path[0], default))
        return self.get(*path[1:], default=default, node=node.get(path[0], {}))

    def sub(self, *path):
        return Config(self.get(*path, default={}))

    def items(self, *path):
        return {k: Config(v)
                for k, v in self.get(*path, default={}).items()}.items()


class Bash:
    class Style:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'

    class Tag:
        ERROR = 'ERROR'
        SUCCESS = 'SUCCESS'
        RUN = 'RUN'
        FILE = 'FILE'

    @staticmethod
    def out(tag, msg, style=None):
        print('{}{} > {}{}'.format(style, tag, msg, style and Bash.Style.ENDC))

    @staticmethod
    def ok(msg):
        Bash.out(Bash.Tag.SUCCESS, msg, Bash.Style.OKGREEN)

    @staticmethod
    def err(msg):
        Bash.out(Bash.Tag.ERROR, msg, Bash.Style.FAIL)

    @staticmethod
    def head(tag, msg):
        Bash.out(tag, msg, Bash.Style.HEADER)


def main():
    controller = Controller()
    controller.run()


if __name__ == '__main__':
    main()
