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
import time
import datetime
from conda.cli.python_api import Commands, run_command


class Build:
    def __init__(self, openstack: bool, template: str, conda_env: pathlib.Path(), packer_path: pathlib.Path(), provisioning: [str], comment: str, publish: bool):
        self.OPENSTACK = openstack
        self.TEMPLATE = template
        self.OS = "-".join(template.split("-", 2)[:2])
        self.comment = comment
        self.PUBLISH = publish
        self.CONDA_ENV = conda_env
        self.provisioning = provisioning
        self.PACKER_PATH = str(conda_env) + \
            "/bin/packer" if conda_env != None else str(packer_path)

    def dry_run(self):
        print(self.assemble_packer_command())
        print(self.assemble_name())

    def assemble_packer_command(self):
        prov_str = ','.join(['"' + x + '"' for x in self.provisioning])
        cmd = [str(self.PACKER_PATH)]
        cmd += ["build"]
        cmd += ["-var='conda_env="
                + str(self.CONDA_ENV)
                + "'"]
        cmd += ["-only="
                + self.TEMPLATE]
        cmd += ['-var="headless=true"' +
                "-var='groups=[" + prov_str + "]'"]
        cmd += ["templates"]
        return " ".join(cmd)

    def assemble_name(self):
        name = ["vgcn"]
        if "generic" in self.provisioning:
            prv = self.provisioning
            prv.remove("generic")
            name += ["+" + x for x in prv]
        else:
            name += ["!generic+" + "+".join(self.provisioning)]
        name += [self.OS]
        name += [self.assemble_timestamp()]
        name += [subprocess.check_output(['git', 'rev-parse',
                                          '--abbrev-ref', 'HEAD']).decode('ascii').strip()]
        name += [subprocess.check_output(['git', 'rev-parse',
                                          '--short', 'HEAD']).decode('ascii').strip()]
        if self.comment != None:
            name += [self.comment]
        return "~".join(name)

    # function that creates a string from the local date + seconds from midnight in the format YYYYMMDD-"seconds from midnight"
    def assemble_timestamp(self):
        today = datetime.date.today()
        seconds_since_midnight = time.time() - time.mktime(today.timetuple())
        return today.strftime("%Y%m%d") + "~" + str(int(seconds_since_midnight))
    # return string with the current seconds from midnight

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

parser_build.add_argument('image', choices=["-".join(x.split("-", 3)[:3]) for x in os.listdir(
    'templates') if x.endswith('-anaconda-ks.cfg')], help='image help')
# another required positional argument is the provisioning. This are the ansible playbooks, which are located in the ansible folder
# and are automatically detected by this script, the options are the file basenames
parser_build.add_argument('provisioning', choices=[x.split(".", 1)[0] for x in os.listdir(
    'ansible') if x.endswith('.yml')], help='provisioning help', nargs='+')
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
# The user has to specify either --conda-env or --packer-path
# --conda-env specifies the conda environment to use
parser_build.add_argument('--conda-env', type=pathlib.Path,
                          help='conda-env help')
# --packer-path specifies the path to the packer binary
parser_build.add_argument('--packer-path', type=pathlib.Path,
                          help='packer-path help')
# --comment is an optional argument to add a comment to the image name
parser_build.add_argument('--comment', type=str, help='comment help')

# Execute the parse_args() method

args = my_parser.parse_args()


def main():
    if args.subparser_name == 'env':
        if args.action == 'install':
            install_conda_env(args.name, args.file)
        elif args.action == 'check':
            check_conda_env()
        elif args.action == 'delete':
            delete_conda_env()
    elif args.subparser_name == 'build':
        if args.dry_run:
            Build(args.openstack, args.image, args.conda_env,
                  args.packer_path, args.provisioning, args.comment, args.publish).dry_run()
        else:
            Build(args.openstack, args.image, args.conda_env,
                  args.packer_path, args.provisioning, args.comment, args.publish).build_image()
    else:
        print('No action specified')


if __name__ == '__main__':
    main()

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


def get_active_branch_name():

    head_dir = Path(".") / ".git" / "HEAD"
    with head_dir.open("r") as f:
        content = f.read().splitlines()

    for line in content:
        if line[0:4] == "ref:":
            return line.partition("refs/heads/")[2]


def delete_conda_env():
    # check if the environment exists
    if Commands().envs()['envs'] != []:
        # if the environment exists, delete the environment
        run_command(Commands().remove, '-n', 'vgcn', '--all')
    else:
        # if the environment does not exist, print a message
        print('The conda environment is not installed')

# Create a function to build the image
