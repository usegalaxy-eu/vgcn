packer {
  required_plugins {
    ansible = {
      source  = "github.com/hashicorp/ansible"
      version = "~> 1"
    }
  }
}

local "disk_size" {
  expression = "${contains(var.groups, "workers-gpu") ? "20G" : "10G"}"
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
    name = "rockylinux-8.6-x86_64"
    vm_name = "rockylinux-8.6-x86_64"
    iso_url = "https://dl.rockylinux.org/vault/rocky/8.6/isos/x86_64/Rocky-8.6-x86_64-boot.iso"
    iso_checksum = "sha256:fe77cc293a2f2fe6ddbf5d4bc2b5c820024869bc7ea274c9e55416d215db0cc5"
    disk_size = "${local.disk_size}"
    boot_command = [
      "<esc><wait>",
      "linux inst.mbr biosdevname=0 net.ifnames=0 ",
      "rootpw=${var.ssh_password} ",
      "inst.ks=http://{{ .HTTPIP }}:{{ .HTTPPort }}/rockylinux-8.6-x86_64-anaconda-ks.cfg",
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
    name = "rockylinux-9.1-x86_64"
    vm_name = "rockylinux-9.1-x86_64"
    iso_url = "https://download.rockylinux.org/pub/rocky/9/isos/x86_64/Rocky-9.1-x86_64-boot.iso"
    iso_checksum = "sha256:a36753d0efbea2f54a3dc7bfaa4dba95efe9aa3d6af331d5c5b147ea91240c21"
    disk_size = "${local.disk_size}"
    boot_command = [
      "<esc><wait>",
      "linux inst.mbr biosdevname=0 net.ifnames=0 ",
      "rootpw=${var.ssh_password} ",
      "inst.ks=http://{{ .HTTPIP }}:{{ .HTTPPort }}/rockylinux-9.1-x86_64-anaconda-ks.cfg",
      "<enter>"
    ]
    shutdown_command = "systemctl poweroff"
  }

  source "source.qemu.base" {
    name = "rockylinux-9.2-x86_64"
    vm_name = "rockylinux-9.2-x86_64"
    iso_url = "https://download.rockylinux.org/pub/rocky/9/isos/x86_64/Rocky-9.2-x86_64-boot.iso"
    iso_checksum = "sha256:11e42da96a7b336de04e60d05e54a22999c4d7f3e92c19ebf31f9c71298f5b42"
    disk_size = "${local.disk_size}"
    boot_command = [
      "<esc><wait>",
      "linux inst.mbr biosdevname=0 net.ifnames=0 ",
      "rootpw=${var.ssh_password} ",
      "inst.ks=http://{{ .HTTPIP }}:{{ .HTTPPort }}/rockylinux-9.2-x86_64-anaconda-ks.cfg",
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

  provisioner "ansible" {
    playbook_file    = "ansible/${local.playbook}"
    user             = "root"
    galaxy_file      = "requirements.yml"
    roles_path       = "ansible/roles/"
    collections_path = "ansible/collections/"
    ansible_env_vars = [
      "ANSIBLE_HOST_KEY_CHECKING=False",
      "ANSIBLE_SCP_EXTRA_ARGS = '-0'",
    ]
    extra_arguments  = "${compact([local.vault_password, var.ansible_extra_args])}"
    groups           = var.groups
  }

  post-processor "manifest" {
      output = "${var.output_directory}/${source.name}.json"
  }
}
