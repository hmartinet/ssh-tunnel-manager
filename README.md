# SSH Tunnel Manager

A tool to manage your recurrent SSH commands with a user configuration file.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

Python 3 and virtualenv.

### Installing

#### Development Install

Install a development environment.

In the project directory, create a virtualenv and activate it.

```
virtualenv venv
./venv/bin/activate
```

Build the project and test it.

```
python setup.py install
stm -h
```

#### Production Install

Install for production in a virtualenv (exmaple for Debian/Ubuntu).


```
sudo apt-get isntall python3-virtualenv
sudo virtualenv ssh-tunnel-manager --python=python3
sudo -H ssh-tunnel-manager/bin/pip install ssh_tunnel_manager
sudo ln -s /opt/ssh-tunnel-manager/bin/stm /usr/bin/stm
```


## Running the tests

No tests at this time...


## Authors

* **Hervé Martinet** - *Initial work* - [GitHub Profile](https://github.com/hmartinet)

See also the list of [contributors](https://github.com/hmartinet/ssh-tunnel-manager/contributors) who participated in this project.

## License

This project is licensed under the GPLv3 License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Dedicate to the time I loose searching ssh command arguments documentation each time I need it.
* My .bash_aliases and my /etc/hosts thank this tool for the slimming cure they took advantage of.
