# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import ssh_tunnel_manager

setup(
    name='ssh_tunnel_manager',
    version=ssh_tunnel_manager.__version__,
    author="Hervé Martinet",
    author_email="herve.martinet@gmail.com",
    description="An utility to manage your SSH tunnels",
    long_description=open('README.md').read(),

    install_requires=['appdirs', 'argcomplete', 'PyYAML'],
    packages=find_packages(),
    # Activate MANIFEST.in
    include_package_data=True,

    # Une url qui pointe vers la page officielle de votre lib
    url='https://github.com/hmartinet/ssh-tunnel-manager',

    # List: https://pypi.python.org/pypi?%3Aaction=list_classifiers.
    classifiers=[
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Topic :: System :: Networking",
    ],

    scripts=[
        'bin/stm',
    ]
)
