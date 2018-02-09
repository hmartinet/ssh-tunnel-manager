#!/usr/bin/python3
# PYTHON_ARGCOMPLETE_OK

import os
import appdirs
import sys
import yaml
import subprocess
import argparse
import argcomplete
from shutil import copyfile

APP_NAME = "SSH Tunnel Manager"
APP_AUTHOR = "Hervé Martinet"
APP_VERSION = "0.1-beta1"


class Controller(object):

    def __init__(self):
        _dir = os.path.dirname(os.path.realpath(__file__))
        conf_dir = os.path.dirname(
            appdirs.user_data_dir(APP_NAME, APP_AUTHOR, version=APP_VERSION))
        if not os.path.exists(conf_dir):
            os.makedirs(conf_dir)
        self.conf_file = '{}/config.yml'.format(conf_dir)
        if not os.path.exists(self.conf_file):
            copyfile('{}/config.yml'.format(_dir), self.conf_file)
        with open(self.conf_file, 'r') as f:
            self.conf = Config(yaml.load(f))
        self.parse_args()

    def parse_args(self):
        self.parser = argparse.ArgumentParser()

        self.parser.add_argument(
            '-c', '--config', action='store_true', dest='config',
            help="edit configuration file")

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

    def run(self, args):
        if self.args.config:
            subprocess.run([self.conf.get('editor'), self.conf_file])
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
        print(BColors.WARNING + BColors.BOLD +
              "\n### {}:{} tunnelized on {}.{}:{} ###\n".format(
                  server.get('ip'), command.get('remote'),
                  self.args.server, Const.STM,
                  self.args.port or command.get('local')) +
              BColors.ENDC)

    def connect(self, cmd):
        print(BColors.HEADER + 'RUN > ' + cmd + BColors.ENDC)
        subprocess.run(cmd.split(' '))


class Config():

    def __init__(self, config):
        self.c = config

    def get(self, *path, default=None, node=None):
        node = node or self.c
        if len(path) == 1:
            return node.get(path[0], default)
        return self.get(*path[1:], default=default, node=node.get(path[0], {}))

    def sub(self, *path):
        return Config(self.get(*path, default={}))

    def items(self, *path):
        return {k: Config(v)
                for k, v in self.get(*path, default={}).items()}.items()


class Const:
    STM = 'stm'


class BColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def main():
    controller = Controller()
    controller.run(sys.argv[1:])


if __name__ == '__main__':
    main()
