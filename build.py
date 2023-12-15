#!/usr/bin/env python
# A commandline script using argparse that builds a vgcn image with packer
# CAUTION: If a directory called 'images' exists in this directory, it will be deleted!
# Required arguments are the template, which are named like the anaconda-ks.cfg files without the
# anaconda-ks.cfg suffix and the provisioning, separated by space and named like the ansible-playbooks
# in the ansible directory without the .yml suffix.
# Optionally you can specify the path to the Packer binary you want to use (--packer-path)
# the path to the conda env you want to use (--conda-env)
# the path to your ssh private key for copying the images to sn06 and
# make them publicly available (--publish)
# you can also source your OpenStack application credentials first and set the (`--openstack`) flag
# to create a raw image in your openstack tenant
# If you have trouble with the ansible provider on your setup, you can specify additional
# --ansible-args="..." to e.g. solve the issues with scp on some distros


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


my_parser = argparse.ArgumentParser(prog='build',
                                    description='Build a VGCN image with Packer and the Ansible provisioner')

my_parser.add_argument('image', choices=["-".join(x.split("-", 3)[:3]) for x in os.listdir(
    'templates') if x.endswith('-anaconda-ks.cfg')], help='image help')
my_parser.add_argument('provisioning', choices=[x.split(".", 1)[0] for x in os.listdir(
    'ansible') if x.endswith('.yml')], help='''
    The playbooks you want to provision.
    The playbook files are located in the ansible folder
    and are automatically detected by this script, the options are the filenames, without .yml suffix
    ''', nargs='+')
my_parser.add_argument('--ansible-args', type=str,
                       help='e.g. --ansible-args="--scp-extra-args=-O" which activates SCP compatibility mode and might be needed on Fedora')
my_parser.add_argument('--openstack', action='store_true',
                       help='Create an image in your OpenStack tenant and upload it. Make sure to source your credentials first')
my_parser.add_argument('--publish', type=pathlib.Path, metavar='PVT_KEY',
                       help='specify the path to your ssh key for sn06')
my_parser.add_argument('--dry-run', action='store_true',
                       help='just print the commands without executing anything')
my_parser.add_argument('--conda-env', type=pathlib.Path,
                       help='specifies the path to  the conda environment to use')
my_parser.add_argument('--packer-path', type=pathlib.Path,
                       help='specifies the path to the packer binary')
my_parser.add_argument('--comment', type=str,
                       help='add a comment to the image name')


args = my_parser.parse_args()


# Spinner thanks to stackoverflow user victor-moyseenko
class Spinner:
    """
    Creates a spinning cursor while the command runs.\n
    Indicates the user that the screen did not freeze or similar.\n
    Especially useful during the image upload, which can take several minutes.\n
    """
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


def run_subprocess_with_spinner(name: str, proc: subprocess.Popen):
    """
    Opens a subprocess and redirect stdout and stderr to Python.\n
    Shows a spinning Cursor while the command runs.\n
    Exits with returncode of subprocess if not equals 0.\n
    """
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
            print(f"{name.rstrip('Ee')}ing...")
            with proc as p:
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
    head_dir = pathlib.Path(DIR_PATH + "/.git/HEAD")
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
        if self.openstack != None:
            print(self.assemble_os_command())
        if self.pvt_key != None:
            print(self.assemble_scp_command())
            print(self.assemble_ssh_command())

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
        """
        Uses a naming scheme described in\n
        https://github.com/usegalaxy-eu/vgcn/issues/78
        """
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

    def build(self):
        self.clean_image_dir()
        run_subprocess_with_spinner("BUILD", subprocess.Popen(self.assemble_packer_build_command(), env=self.assemble_packer_envs(),
                                                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True, shell=True))

    def convert(self):
        run_subprocess_with_spinner(name="CONVERT", proc=subprocess.Popen(self.assemble_convert_command(),
                                                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True, shell=True))

    def clean_image_dir(self):
        if os.path.exists(DIR_PATH + "/images"):
            shutil.rmtree(DIR_PATH + "/images")

    def upload_to_OS(self):
        run_subprocess_with_spinner("OPENSTACK IMAGE CREATE", subprocess.Popen(self.assemble_os_command(),
                                                                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True, shell=True))

    def pvt_key(self):
        run_subprocess_with_spinner("PUBLISH", subprocess.Popen(self.assemble_scp_command(),
                                                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True, shell=True))
        run_subprocess_with_spinner("PERMISSION CHANGE", subprocess.Popen(self.assemble_ssh_command(),
                                                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True, shell=True))


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
