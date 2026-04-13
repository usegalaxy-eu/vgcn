packer {
  required_plugins {
    ansible = {
      source  = "github.com/hashicorp/ansible"
      version = "~> 1"
    }
  }
}

local "disk_size" {
  expression = "${contains(var.groups, "workers-gpu") ? "40G" : "10G"}"
}

build {
  source "source.qemu.base" {
    name = "centos-8.5.2111-x86_64"
    vm_name = "centos-8.5.2111-x86_64"
    iso_url = "https://vault.centos.org/8.5.2111/isos/x86_64/CentOS-8.5.2111-x86_64-boot.iso"
    iso_checksum = "sha256:9602c69c52d93f51295c0199af395ca0edbe35e36506e32b8e749ce6c8f5b60a"
    disk_size = "${local.disk_size}"
    boot_command = [
      "<esc><wait>",
      "linux inst.mbr biosdevname=0 net.ifnames=0 ",
      "rootpw=${var.ssh_password} ",
      "inst.ks=http://{{ .HTTPIP }}:{{ .HTTPPort }}/centos-8.5.2111-anaconda-ks.cfg",
      "<enter>"
    ]
    shutdown_command = "systemctl poweroff"
  }

  source "source.qemu.base" {
    name = "almalinux-8.8-x86_64"
    vm_name = "almalinux-8.8-x86_64"
    iso_url = "https://mirror.hs-esslingen.de/Mirrors/almalinux/8/isos/x86_64/AlmaLinux-8.8-x86_64-boot.iso"
    iso_checksum = "sha256:016e59963c2c3bd4c99c18ac957573968e23da51131104568fbf389b11df3e05"
    disk_size = "${local.disk_size}"
    boot_command = [
      "<tab>",
      "inst.text net.ifnames=0 inst.gpt ",
      "inst.ks=http://{{ .HTTPIP }}:{{ .HTTPPort }}/almalinux-8.8-x86_64-anaconda-ks.cfg",
      "<enter><wait>"
    ]
    shutdown_command = "systemctl poweroff"
  }

  source "source.qemu.base" {
    name = "rockylinux-9.6-x86_64"
    vm_name = "rockylinux-9.6-x86_64"
    iso_url = "https://dl.rockylinux.org/vault/rocky/9.6/isos/x86_64/Rocky-9.6-x86_64-boot.iso"
    iso_checksum = "0fad8d8b19a94a0222ea37152cdf5601229fe0178b651dc476e1cba41d2e6067"
    disk_size = "${local.disk_size}"
    boot_command = [
      "<esc><wait>",
      "linux inst.mbr biosdevname=0 net.ifnames=0 ",
      "rootpw=${var.ssh_password} ",
      "inst.ks=http://{{ .HTTPIP }}:{{ .HTTPPort }}/rockylinux-9.6-x86_64-anaconda-ks.cfg",
      "<enter>"
    ]
    shutdown_command = "systemctl poweroff"
  }

  source "source.qemu.base" {
    name = "rockylinux-9-latest-x86_64"
    vm_name = "rockylinux-9-latest-x86_64"
    iso_url = "https://download.rockylinux.org/pub/rocky/9/isos/x86_64/Rocky-9-latest-x86_64-boot.iso"
    iso_checksum = "sha256:628c069c9685477360640a6b58dc919692a11c44b49a50a024b5627ce3c27d5f"
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
    name = "rockylinux-10.1-x86_64"
    vm_name = "rockylinux-10.1-x86_64"
    iso_url = "https://download.rockylinux.org/pub/rocky/10/isos/x86_64/Rocky-10.1-x86_64-boot.iso"
    iso_checksum = "sha256:18543988d9a1a5632d142c3dc288136dcc48ab71628f92ebcd40ada7f4ecd110"
    disk_size = "${local.disk_size}"
    boot_command = [
      "<esc><wait>e",
      "<down><down><end><wait>",
      " inst.ks=http://{{ .HTTPIP }}:{{ .HTTPPort }}/rockylinux-10.1-x86_64-anaconda-ks.cfg",
      " rootpw=${var.ssh_password} ",
      "<leftCtrlOn>x<leftCtrlOff>"
    ]
    shutdown_command = "systemctl poweroff"
  }

  provisioner "shell" {
      inline = [
        "usermod -u 99 $(id -nu 999 )",
        "groupmod -g 99 $(getent group 999 | cut -d: -f1)"
        "dnf -y update",
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
      "ANSIBLE_SCP_EXTRA_ARGS = '-0'",
    ]
    extra_arguments  = "${compact([local.vault_password, var.ansible_extra_args, local.ansible_image_name])}"
    groups           = var.groups
  }

  post-processor "manifest" {
      output = "${var.output_directory}/${source.name}.json"
  }
}
