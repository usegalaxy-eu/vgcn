packer {
  required_plugins {
    ansible = {
      source  = "github.com/hashicorp/ansible"
      version = "~> 1"
    }
  }
}

build {
  source "source.qemu.base" {
    name = "rockylinux-9-latest-x86_64"
    vm_name = "rockylinux-9-latest-x86_64"
    iso_url = "https://download.rockylinux.org/pub/rocky/9/isos/x86_64/Rocky-9-latest-x86_64-boot.iso"
    iso_checksum = "file:https://download.rockylinux.org/pub/rocky/9/isos/x86_64/Rocky-9-latest-x86_64-boot.iso.CHECKSUM"
    disk_size = "${local.disk_size}"
    boot_command = [
      "<esc><wait>",
      "linux inst.mbr biosdevname=0 net.ifnames=0 ",
      "rootpw=${var.ssh_password} ",
      "inst.ks=http://{{ .HTTPIP }}:{{ .HTTPPort }}/rockylinux-9-latest-x86_64-anaconda-ks.cfg",
      "<enter>"
    ]
    shutdown_command = "systemctl poweroff"
  }

  source "source.qemu.base" {
    name = "rockylinux-10-latest-x86_64"
    vm_name = "rockylinux-10-latest-x86_64"
    iso_url = "https://download.rockylinux.org/pub/rocky/10/isos/x86_64/Rocky-10-latest-x86_64-boot.iso"
    iso_checksum = "file:https://download.rockylinux.org/pub/rocky/10/isos/x86_64/Rocky-10-latest-x86_64-boot.iso.CHECKSUM"
    disk_size = "${local.disk_size}"
    boot_command = [
      "<esc><wait>e",
      "<down><down><end><wait>",
      " inst.ks=http://{{ .HTTPIP }}:{{ .HTTPPort }}/rockylinux-10-latest-x86_64-anaconda-ks.cfg",
      " rootpw=${var.ssh_password} ",
      "<leftCtrlOn>x<leftCtrlOff>"
    ]
    shutdown_command = "systemctl poweroff"
  }

  provisioner "shell" {
    inline = [
      "usermod -u 99 $(id -nu 999 )",
      "groupmod -g 99 $(getent group 999 | cut -d: -f1)",
      "uname -r",
      "sudo dnf update -y",
      "dnf -y install epel-release",
      "dnf config-manager --set-enabled crb", # Enable CRB for dependencies
      "dnf -y install wget ansible-core",     # Use ansible-core for v10
      "echo 'System prepared for Ansible'",
    ]
  }

  provisioner "ansible" {
    playbook_file    = "ansible/${local.playbook}"
    user             = "root"
    galaxy_file      = "requirements.yml"
    roles_path       = "ansible/roles/"
    collections_path = "ansible/collections/"
    ansible_env_vars = [
      "ANSIBLE_HOST_KEY_CHECKING=False",
      "ANSIBLE_SSH_TRANSFER_METHOD=scp",
      "ANSIBLE_SCP_IF_SSH=True",
      "ANSIBLE_PIPELINING=True",
      "ANSIBLE_SCP_EXTRA_ARGS=-O",
    ]
    extra_arguments  = "${compact([local.vault_password, var.ansible_extra_args, local.ansible_image_name])}"
    groups           = var.groups
  }

  post-processor "manifest" {
      output = "${var.output_directory}/${source.name}.json"
  }
}
