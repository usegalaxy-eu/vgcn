#!/usr/bin/env python
# A command line script that builds a VGCN image with Packer.
# CAUTION: If a directory called 'images' exists in this directory, it will be deleted!
# Required arguments are a Packer build (builds are defined in templates/build.pkr.hcl)
# and the provisioning Ansible playbooks (located in the ansible directory, passed
# without the .yml suffix).
# Optionally you can specify the path to the Packer binary you want to use (--packer-path)
# the path to the conda env you want to use (--conda-env)
# the path to your ssh private key for copying the images to sn06 and
# make them publicly available (--publish)
# you can also source your OpenStack application credentials first and set the (`--openstack`) flag
# to create a raw image in your openstack tenant
# If you have trouble with the ansible provider on your setup, you can specify additional
# --ansible-args="..." to e.g. solve the issues with scp on some distros


import argparse
import contextlib
import datetime
import os
import pathlib
import shutil
import signal
import subprocess
import sys
import threading
import time

DIR_PATH = pathlib.Path(__file__).parent.absolute()

STATIC_DIR = pathlib.Path("/data/dnb01/vgcn/").absolute()

SSH_HOST = "sn06.galaxyproject.eu"

SSH_USER = "root"


def make_parser() -> argparse.ArgumentParser:
    my_parser = argparse.ArgumentParser(
        prog="build",
        description="Build a VGCN image with Packer and the Ansible provisioner",
    )

    my_parser.add_argument(
        "image",
        help="image help",
    )
    my_parser.add_argument(
        "provisioning",
        choices=[
            x.split(".", 1)[0] for x in os.listdir("ansible") if x.endswith(".yml")
        ],
        help="""
        The playbooks you want to provision.
        The playbook files are located in the ansible folder
        and are automatically detected by this script, the options are the filenames, without .yml suffix
        """,
        nargs="+",
    )
    my_parser.add_argument(
        "--ansible-args",
        type=str,
        help='e.g. --ansible-args="--scp-extra-args=-O" which activates SCP compatibility mode and might be needed on Fedora',
    )
    my_parser.add_argument(
        "--openstack",
        action="store_true",
        help="Create an image in your OpenStack tenant and upload it. Make sure to source your credentials first",
    )
    my_parser.add_argument(
        "--publish",
        type=pathlib.Path,
        metavar="PVT_KEY",
        help="specify the path to your ssh key for sn06",
    )
    my_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="just print the commands without executing anything",
    )
    my_parser.add_argument(
        "--conda-env",
        type=pathlib.Path,
        help="specifies the path to  the conda environment to use",
    )
    my_parser.add_argument(
        "--comment", type=str, help="add a comment to the image name"
    )
    my_parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Don't use the spinner, but still print logs.",
    )

    return my_parser


# Spinner class from https://stackoverflow.com/a/39504463 by Victor Moyseenko, subject to CC BY-SA 4.0 license.
class Spinner:
    """
    Creates a spinning cursor while the command runs.
    Indicates the user that the screen did not freeze or similar.
    Especially useful during the image upload, which can take several minutes.
    """

    busy = False
    delay = 0.1

    @staticmethod
    def spinning_cursor():
        while 1:
            for cursor in "|/-\\":
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
            sys.stdout.write("\b")
            sys.stdout.flush()

    def __enter__(self):
        self.busy = True
        threading.Thread(target=self.spinner_task).start()

    def __exit__(self, exception, value, tb):
        self.busy = False
        time.sleep(self.delay)
        if exception is not None:
            return False


def run_subprocess_with_spinner(name: str, proc: subprocess.Popen, show_spinner: bool):
    """
    Opens a subprocess and redirect stdout and stderr to Python.
    Shows a spinning Cursor while the command runs.
    Exits with returncode of subprocess if not equals 0.
    """

    try:
        p = None
        # Register handler to pass keyboard interrupt to the subprocess

        def handler(sig, frame):
            print(f"================= {name} ABORTED BY USER ====================")
            if p:
                p.send_signal(signal.SIGINT)
            else:
                raise KeyboardInterrupt.add_note()

        signal.signal(signal.SIGINT, handler)
        context_mgr = Spinner() if show_spinner else contextlib.suppress()
        with context_mgr:
            print(f"{name.rstrip('Ee')}ing...")
            with proc as p:
                for line in iter(p.stdout.readline, b""):
                    # Print the line to the console
                    sys.stdout.buffer.write(line)
                for line in iter(p.stderr.readline, b""):
                    # Print the error output to the console
                    sys.stderr.buffer.write(line)
                returncode = p.wait()
                if returncode:
                    print(
                        f"===================== {name} FAILED ========================="
                    )
                    sys.exit(returncode)
                else:
                    print(
                        f"===================== {name} SUCCESSFUL ====================="
                    )
    finally:
        signal.signal(signal.SIGINT, signal.SIG_DFL)


class Build:
    def __init__(
        self,
        openstack: bool,
        template: str,
        conda_env: pathlib.Path,
        provisioning: [str],
        comment: str,
        pvt_key: pathlib.Path,
        ansible_args: str,
        show_spinner: bool,
    ):
        self.openstack = openstack
        self.template = template
        self.comment = comment
        self.pvt_key = pvt_key
        self.provisioning = provisioning
        self.ansible_args = ansible_args
        self.image_name = self.assemble_name()
        self.image_path = DIR_PATH / f"{self.image_name}.raw"
        self.show_spinner = show_spinner
        if conda_env:
            self.qemu_path = f"{conda_env}/bin/qemu-img"
            self.openstack_path = f"{conda_env}/bin/openstack"
            self.packer_path = f"{conda_env}/bin/packer"
        else:
            self.packer_path = shutil.which("packer")
            self.openstack_path = shutil.which("openstack")
            self.qemu_path = shutil.which("qemu-img")

    def dry_run(self):
        print(self.assemble_packer_envs())
        print(self.assemble_packer_build_command())
        print(self.image_name)
        print(self.assemble_convert_command())
        if self.openstack:
            print(self.assemble_os_command())
        if self.pvt_key:
            print(self.assemble_scp_command())
            print(self.assemble_ssh_command())

    def assemble_packer_init_command(self):
        return " ".join(
            [
                f"{self.packer_path}",
                f"init",
                f"{DIR_PATH / 'templates'}",
            ]
        )

    def assemble_packer_build_command(self):
        return " ".join(
            [
                f"{self.packer_path}",
                f"build",
                f"-only=qemu.{self.template}",
                f"{DIR_PATH / 'templates'}",
            ]
        )

    def assemble_convert_command(self):
        return " ".join(
            [
                f"{self.qemu_path}",
                f"convert",
                f"-O",
                f"raw",
                f"./images/{self.template}",
                f"{self.image_path}",
            ]
        )

    def assemble_os_command(self):
        return " ".join(
            [
                f"{self.openstack_path}",
                f"image",
                f"create",
                f"--file",
                f"{self.image_path}",
                f"{self.image_name}",
            ]
        )

    def assemble_packer_envs(self):
        env = os.environ.copy()
        env["PACKER_PLUGIN_PATH"] = f"{DIR_PATH}/packer_plugins"
        env[
            "PKR_VAR_groups"
        ] = f"""[{','.join('"' + x + '"' for x in self.provisioning)}]"""
        env["PKR_VAR_headless"] = "true"
        if self.ansible_args:
            env["PKR_VAR_ansible_extra_args"] = self.ansible_args
        return env

    def assemble_name(self):
        """
        Uses a naming scheme described in
        https://github.com/usegalaxy-eu/vgcn/issues/78
        """
        provisioning = self.provisioning.copy()
        if "generic" not in self.provisioning:
            provisioning.insert(0, "!generic")
        name = [
            "vgcn",
            self.template,
            f"+{'+'.join(provisioning)}",
            self.assemble_timestamp(),
            subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
            .decode("ascii")
            .strip(),
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
            .decode("ascii")
            .strip(),
        ]
        if self.comment:
            name += [self.comment]
        return "~".join(name)

    def assemble_scp_command(self):
        return " ".join(
            [
                f"scp",
                f"-i",
                f"{self.pvt_key}",
                f"{self.image_path}",
                f"{SSH_USER}@{SSH_HOST}:{STATIC_DIR / self.image_name}",
            ]
        )

    def assemble_ssh_command(self):
        return " ".join(
            [
                f"ssh",
                f"-i",
                f"{self.pvt_key}",
                f"{SSH_USER}@{SSH_HOST}",
                f"chmod",
                f"ugo+r",
                f"{STATIC_DIR / self.image_name}",
            ]
        )

    def assemble_timestamp(self):
        commit_time = (
            subprocess.check_output(["git", "show", "--no-patch", "--format=%ct"])
            .decode("ascii")
            .strip()
        )
        commit_time = int(commit_time)
        commit_time = datetime.datetime.fromtimestamp(commit_time)

        commit_date = commit_time.date()
        commit_date_midnight = datetime.datetime(
            commit_date.year, commit_time.month, commit_time.day
        )

        seconds_since_midnight = int(
            (commit_time - commit_date_midnight).total_seconds()
        )

        return f"{commit_time.date().strftime('%Y%m%d')}" f"~{seconds_since_midnight}"

    def build(self):
        self.clean_image_dir()
        run_subprocess_with_spinner(
            "INITIALIZE",
            subprocess.Popen(
                self.assemble_packer_init_command(),
                env=self.assemble_packer_envs(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True,
                shell=True,
            ),
            show_spinner=self.show_spinner,
        )
        run_subprocess_with_spinner(
            "BUILD",
            subprocess.Popen(
                self.assemble_packer_build_command(),
                env=self.assemble_packer_envs(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True,
                shell=True,
            ),
            show_spinner=self.show_spinner,
        )

    def convert(self):
        run_subprocess_with_spinner(
            name="CONVERT",
            proc=subprocess.Popen(
                self.assemble_convert_command(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True,
                shell=True,
            ),
            show_spinner=self.show_spinner,
        )

    def clean_image_dir(self):
        if (DIR_PATH / "images").exists():
            shutil.rmtree(DIR_PATH / "images")

    def upload_to_OS(self):
        # Checking this, because OS is failing silently
        env = os.environ.copy()
        if not (
            "OS_AUTH_URL" in env
            and "OS_APPLICATION_CREDENTIAL_ID" in env
            and "OS_APPLICATION_CREDENTIAL_SECRET" in env
        ):
            print("OS credentials missing in environment vars")
            sys.exit(1)
        run_subprocess_with_spinner(
            "OPENSTACK IMAGE CREATE",
            subprocess.Popen(
                self.assemble_os_command(),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True,
                shell=True,
            ),
            show_spinner=self.show_spinner,
        )

    def publish(self):
        run_subprocess_with_spinner(
            "PUBLISH",
            subprocess.Popen(
                self.assemble_scp_command(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True,
                shell=True,
            ),
            show_spinner=self.show_spinner,
        )
        run_subprocess_with_spinner(
            "PERMISSION CHANGE",
            subprocess.Popen(
                self.assemble_ssh_command(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True,
                shell=True,
            ),
            show_spinner=self.show_spinner,
        )


def main():
    my_parser = make_parser()
    args = my_parser.parse_args()
    image = Build(
        openstack=args.openstack,
        template=args.image,
        conda_env=args.conda_env,
        provisioning=args.provisioning,
        comment=args.comment,
        ansible_args=args.ansible_args,
        pvt_key=args.publish,
        show_spinner=not args.quiet,
    )
    if args.dry_run:
        image.dry_run()
    else:
        image.build()
        image.convert()
        if args.openstack:
            image.upload_to_OS()
        if args.publish:
            image.publish()


if __name__ == "__main__":
    main()
