#!/usr/bin/env python
# Create a commandline script using argparse that
# has two main functionalities: create a conda environment and build an image with packer
# The script should have two subcommands: env and build
# the env subcommand can either install, check or delete the conda environment
# install creates an environment called "vgcn" with ansible and packer installed
# the env subcommand utilizes conda python api
# check checks if the environment exists and if the packages are installed
# delete deletes the environment

import argparse
import os
import pathlib
import subprocess
import time
import sys
import shutil
import datetime
import signal
import threading


DIR_PATH = os.path.dirname(os.path.realpath(__file__))


# Create the parser
my_parser = argparse.ArgumentParser(prog='build',
                                    description='Create a conda environment and build an image with packer')

# Add the arguments
my_parser.add_argument('image', choices=["-".join(x.split("-", 3)[:3]) for x in os.listdir(
    'templates') if x.endswith('-anaconda-ks.cfg')], help='image help')
# another required positional argument is the provisioning. This are the ansible playbooks, which are located in the ansible folder
# and are automatically detected by this script, the options are the file basenames
my_parser.add_argument('provisioning', choices=[x.split(".", 1)[0] for x in os.listdir(
    'ansible') if x.endswith('.yml')], help='provisioning help', nargs='+')
# --ansible-args lets the user pass additional args to the packer ansible provisioner, useful e.g. in case of ssh problems
my_parser.add_argument('--ansible-args', type=str,
                       help='e.g. --ansible-args="--scp-extra-args=-O" which activates SCP compatibility mode and might be needed on Fedora')
# the --openstack option specifies if the image should be uploaded to openstack or not
my_parser.add_argument('--openstack', action='store_true',
                       help='openstack help')
# another option is to publish the image to /static/vgcn via scp
my_parser.add_argument('--publish', type=pathlib.Path,
                       help='specify the path to your ssh key for sn06')
# with the --dry-run option the script will only print the commands that would be executed
# and the resulting image file name according to the naming scheme
my_parser.add_argument('--dry-run', action='store_true',
                       help='dry-run help')
# The user has to specify either --conda-env or --packer-path
# --conda-env specifies the conda environment to use
my_parser.add_argument('--conda-env', type=pathlib.Path,
                       help='conda-env help')
# --packer-path specifies the path to the packer binary
my_parser.add_argument('--packer-path', type=pathlib.Path,
                       help='packer-path help')
# --comment is an optional argument to add a comment to the image name
my_parser.add_argument('--comment', type=str, help='comment help')

# Execute the parse_args() method

args = my_parser.parse_args()


# Create a function to install the conda environment

# Create a function to build the image

# Spinner thanks to stackoverflow user victor-moyseenko
class Spinner:
    busy = False
    delay = 0.1

    @staticmethod
    def spinning_cursor():
        while 1:
            for cursor in '|/-\\':
                yield cursor

    def __init__(self, delay=None):
        self.spinner_generator = self.spinning_cursor()
        if delay and float(delay):
            self.delay = delay

    def spinner_task(self):
        while self.busy:
            sys.stdout.write(next(self.spinner_generator))
            sys.stdout.flush()
            time.sleep(self.delay)
            sys.stdout.write('\b')
            sys.stdout.flush()

    def __enter__(self):
        self.busy = True
        threading.Thread(target=self.spinner_task).start()

    def __exit__(self, exception, value, tb):
        self.busy = False
        time.sleep(self.delay)
        if exception is not None:
            return False


def execute_cmd(name: str, proc: subprocess.Popen):
    # Open a subprocess and redirect stdout and stderr to Python
    try:
        p = None
        # Register handler to pass keyboard interrupt to the subprocess

        def handler(sig, frame):
            print(f"===================== {
                  name} ABORTED BY USER =========================")
            if p:

                p.send_signal(signal.SIGINT)
            else:
                raise KeyboardInterrupt.add_note()
        signal.signal(signal.SIGINT, handler)
        with Spinner():
            print(f"{name}ing...")
            with proc as p:
               # Loop through the readable streams in real - time
                for line in iter(p.stdout.readline, b''):
                    # Print the line to the console
                    sys.stdout.buffer.write(line)
                for line in iter(p.stderr.readline, b''):
                    # Print the error output to the console
                    sys.stderr.buffer.write(line)
                if p.wait():
                    raise Exception(f"===================== {
                        name} FAILED =========================")
                else:
                    print(f"===================== {
                          name} SUCCESSFUL =========================")
    finally:
        signal.signal(signal.SIGINT, signal.SIG_DFL)


def get_active_branch_name():
    head_dir = pathlib.Path(".") / ".git" / "HEAD"
    with head_dir.open("r") as f:
        content = f.read().splitlines()

    for line in content:
        if line[0:4] == "ref:":
            return line.partition("refs/heads/")[2]


class Build:
    def __init__(self, openstack: bool, template: str, conda_env: pathlib.Path, packer_path: pathlib.Path, provisioning: [str], comment: str, pvt_key: pathlib.Path, ansible_args: str):
        self.openstack = openstack
        self.template = template
        self.os = "-".join(template.split("-", 2)[:2])
        self.comment = comment
        self.pvt_key = pvt_key
        self.conda_env = conda_env
        self.provisioning = provisioning
        self.ansible_args = ansible_args
        self.PACKER_PATH = str(conda_env) + \
            "/bin/packer" if conda_env != None else str(packer_path)
        self.image_name = self.assemble_name()
        self.image_path = pathlib.Path(
            DIR_PATH + "/" + self.image_name + '.raw')

    def dry_run(self):
        print(self.assemble_packer_envs())
        print(self.assemble_packer_build_command())
        print(self.image_name)
        print(self.assemble_convert_command())

    def assemble_packer_init(self):
        cmd = str(self.PACKER_PATH)
        cmd += " init "
        cmd += DIR_PATH + "/templates"
        return cmd

    def assemble_packer_build_command(self):
        cmd = [str(self.PACKER_PATH), "build"]
        cmd.append("-only=qemu." + self.template)
        cmd.append(DIR_PATH + "/templates")
        return " ".join(cmd)

    def assemble_convert_command(self):
        cmd = [str(shutil.which("qemu-img"))]
        cmd.append("convert")
        cmd.append("-O")
        cmd.append("raw")
        cmd.append("./images/" + self.template)
        cmd.append(str(self.image_path))
        return " ".join(cmd)

    def assemble_os_command(self):
        return ["openstack", "image", "create", "--file",
                str(self.image_path), self.image_name]

    def assemble_packer_envs(self):
        env = os.environ.copy()
        env["PACKER_PLUGIN_PATH"] = DIR_PATH + "/packer_plugins"
        env["PKR_VAR_groups"] = "[" + \
            ','.join(["\"" + x + "\"" for x in self.provisioning]) + "]"
        env["PKR_VAR_headless"] = 'true'
        if self.ansible_args != None:
            env["PKR_VAR_ansible_extra_args"] = self.ansible_args
        return env

    def assemble_name(self):
        name = ["vgcn"]
        if "generic" in self.provisioning:
            prv = self.provisioning
            prv.remove("generic")
            name += ["+" + x for x in prv]
        else:
            name += ["!generic+" + "+".join(self.provisioning)]
        name += [self.os]
        name += [self.assemble_timestamp()]
        name += [subprocess.check_output(['git', 'rev-parse',
                                          '--abbrev-ref', 'HEAD']).decode('ascii').strip()]
        name += [subprocess.check_output(['git', 'rev-parse',
                                          '--short', 'HEAD']).decode('ascii').strip()]
        if self.comment != None:
            name += [self.comment]
        return "~".join(name)

    def assemble_scp_command(self):
        return ["scp", self.image_path,
                "sn06.usegalaxy.eu:/data/dnb01/vgcn/" + os.path.basename(self.image_path)]

    def assemble_ssh_command(self):
        cmd = ["ssh"]
        cmd.append("-i")
        cmd.append(str(self.pvt_key))
        cmd.append("sn06.galaxyproject.eu")
        cmd.append("chmod")
        cmd.append("ugo+r")
        cmd.append("/data/dnb01/vgcn/" + os.path.basename(self.image_path))
        return cmd

    def assemble_timestamp(self):
        today = datetime.date.today()
        seconds_since_midnight = time.time() - time.mktime(today.timetuple())
        return today.strftime("%Y%m%d") + "~" + str(int(seconds_since_midnight))
    # return string with the current seconds from midnight

    def convert(self):
        execute_cmd(name="CONVERT", proc=subprocess.Popen(self.assemble_convert_command(),
                                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True))

    def build(self):
        try:
            self.clean_image_dir()
            execute_cmd("BUILD", subprocess.Popen(self.assemble_packer_build_command(), env=self.assemble_packer_envs(),
                                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True))
        except BaseException:
            self.clean_image_dir()
            raise Exception("Cleaned faulty or unfinished images")

    def clean_image_dir(self):
        if os.path.exists("./images"):
            shutil.rmtree("./images")

    def upload_to_OS(self):
        execute_cmd("OPENSTACK IMAGE CREATE", subprocess.Popen(self.assemble_os_command(),
                                                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True))

    def pvt_key(self):
        execute_cmd("PUBLISH", subprocess.Popen(self.assemble_scp_command(),
                                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True))
        execute_cmd("PERMISSION CHANGE", subprocess.Popen(self.assemble_ssh_command(),
                                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True))


def main():
    image = Build(openstack=args.openstack, template=args.image, conda_env=args.conda_env,
                  packer_path=args.packer_path, provisioning=args.provisioning, comment=args.comment,
                  ansible_args=args.ansible_args, pvt_key=args.publish)
    if args.dry_run:
        image.dry_run()
    else:
        image.build()
        image.convert()
        if args.openstack:
            image.upload_to_OS()
        if args.publish:
            image.pvt_key()


if __name__ == '__main__':
    main()
