# Create a commandline script using argparse that
# has two main functionalities: create a conda environment and build an image with packer
# The script should have two subcommands: env and build
# the env subcommand can either install, check or delete the conda environment
# install creates an envornment called "vgcn" with ansible and packer installed
# the env subcommand utilizes conda python api
# check checks if the environment exists and if the packages are installed
# delete deletes the environment

import argparse
import os
import pathlib
import subprocess
import sys
import time
import datetime
import yaml
from conda.cli.python_api import Commands, run_command


class Build:
    def __init__(self, openstack: bool, template: str, conda_env: pathlib.Path(), packer_path: pathlib.Path(), provisioning: list[str]):
        self.OPENSTACK = openstack
        self.TEMPLATE = template
        self.OS = "-".join(template.split("-", 2)[:2])
        self.CONDA_ENV = conda_env
        self.provisioning = provisioning
        self.PACKER_PATH = conda_env + \
            "/bin/packer" if conda_env != None else str(packer_path)

    def dry_run(self):
        print(self.assemble_packer_command)

    def assemble_packer_command(self):
        prov_str = ','.join(f'"{x}"' for x in provisioning)
        cmd = self.CONDA_ENV
        cmd = cmd + "/bin/packer"
        cmd = "packer build " +\
            "-only=" + self.TEMPLATE +\
            '-var="headless=true"' +\
            "-var='groups=[" + prov_str + "]'" +\
            "templates"
        return cmd

    def assemble_name(self):
        name = "vgcn~"
        pv = self.provisioning
        if "generic" in self.provisioning:
            name = name + "+".join(self.provisioning.remove("generic"))
        else:
            name = name + "!generic" + "+".join(self.provisioning)
        name = name + self.OS
        name = name + self.assemble_timestamp()

    # function that creates a string from the local date + seconds from midnight in the format YYYYMMDD-"seconds from midnight"
    def assemble_timestamp(self):
        today = datetime.date.today()
        seconds_since_midnight = time.time() - time.mktime(today.timetuple())
        return today.strftime("%Y%m%d") + "-" + str(int(seconds_since_midnight))
    # return string with the current seconds from midnight

    def assemble_seconds(self):


    def execute_cmd(self):
        return subprocess.run(self.assemble_packer_command(), capture_output=True)

    def build_image(self):
        result = self.execute_cmd()
        if result.returncode != 0:
            raise ValueError(result.stderr)
        else:
            print(result.stdout)


# Create the parser
my_parser = argparse.ArgumentParser(prog='build',
                                    description='Create a conda environment and build an image with packer')

# Add the arguments


# Create subparsers

subparsers = my_parser.add_subparsers(
    help='sub-command help', dest='subparser_name')

# Create the parser for the "env" command
parser_env = subparsers.add_parser('env', help='env help')
parser_env.add_argument(
    'action', choices=['install', 'check', 'delete'], help='action help')

# Create the parser for the "install" command
parser_install = subparsers.add_parser('install', help='install help')
# the install subcommand takes optional arguments for the conda environment name and the conda environment file
parser_install.add_argument('action', choices=['install'], help='action help')
parser_install.add_argument('-n', '--name', type=str, help='name help')
parser_install.add_argument('-f', '--file', type=str, help='file help')

# Create the parser for the "check" command
parser_check = subparsers.add_parser('check', help='check help')
parser_check.add_argument('action', choices=['check'], help='action help')

# Create the parser for the "delete" command
parser_delete = subparsers.add_parser('delete', help='delete help')
parser_delete.add_argument('action', choices=['delete'], help='action help')


# Create the parser for the "build" command

parser_build = subparsers.add_parser('build', help='build help')
parser_build.add_argument('action', choices=['build'], help='action help')
# the image argument is required and one of the automatically detected images in the templates folder
# this script uses a function to automatically detect *.cfg files and strips the "-anaconda-ks.cfg" to make it a choice for the parser
parser_build.add_argument('image', choices=[x[:-16] for x in os.listdir(
    'templates') if x.endswith('-anaconda-ks.cfg')], help='image help')
# another required positional argument is the provisioning. This are the ansible playbooks, which are located in the ansible folder
# and are automatically detected by this script, the options are the file basenames
parser_build.add_argument('provisioning', choices=[x[:-3] for x in os.listdir(
    'ansible') if x.endswith('.yml')], help='provisioning help')
# the --openstack option specifies if the image should be uploaded to openstack or not
parser_build.add_argument('--openstack', action='store_true',
                          help='openstack help')
# another option is to publish the image to /static/vgcn via scp
parser_build.add_argument('--publish', action='store_true',
                          help='publish help')
# with the --dry-run option the script will only print the commands that would be executed
# and the resulting image file name according to the naming scheme
parser_build.add_argument('--dry-run', action='store_true',
                          help='dry-run help')

# Execute the parse_args() method

args = my_parser.parse_args()

# Create a function to install the conda environment


def install_conda_env(name, file):
    # check if the environment exists
    if Commands().envs()['envs'] != []:
        # if the environment exists, check if the packages are installed
        if Commands().list()['packages'] == ['ansible', 'packer']:
            print('The conda environment is already installed')
        else:
            # if the environment exists but the packages are not installed, install the packages
            run_command(Commands().install, 'ansible', 'packer')
    else:
        # if the environment does not exist, create the environment and install the packages
        run_command(Commands().create, '-n', name, '--file', file)
        run_command(Commands().install, 'ansible', 'packer')

# Create a function to check if the conda environment exists and if the packages are installed


def check_conda_env():
    # check if the environment exists
    if Commands().envs()['envs'] != []:
        # if the environment exists, check if the packages are installed
        if Commands().list()['packages'] == ['ansible', 'packer']:
            print('The conda environment is installed')
        else:
            # if the environment exists but the packages are not installed, install the packages
            run_command(Commands().install, 'ansible', 'packer')
    else:
        # if the environment does not exist, print a message
        print('The conda environment is not installed')

# Create a function to delete the conda environment


def delete_conda_env():
    # check if the environment exists
    if Commands().envs()['envs'] != []:
        # if the environment exists, delete the environment
        run_command(Commands().remove, '-n', 'vgcn', '--all')
    else:
        # if the environment does not exist, print a message
        print('The conda environment is not installed')

# Create a function to build the image
