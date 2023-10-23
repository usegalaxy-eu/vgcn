variable "output_directory" {
  type    = string
  default = "images"
}

variable "boot_wait" {
  type    = string
  default = "10s"
}

variable "cpus" {
  type    = string
  default = "2"
}

variable "memory" {
  type    = string
  default = "2048"
}

variable "ssh_username" {
  type    = string
  default = "root"
}

variable "ssh_password" {
  type    = string
  default = "password"
}

variable "ssh_timeout" {
  type    = string
  default = "25m"
}

variable "http_dir" {
  type    = string
  default = "templates"
}

packer {
  required_plugins {
    qemu = {
      version = "~> 1"
      source  = "github.com/hashicorp/qemu"
    }
  }
}

source "qemu" "base" {
  output_directory   = "${var.output_directory}"
  accelerator        = "kvm"
  format             = "qcow2"
  disk_interface     = "virtio"
  net_device         = "virtio-net"
  headless           = "${var.headless}"
  http_directory     = "${var.http_dir}"
  boot_wait          = "${var.boot_wait}"
  ssh_timeout        = "${var.ssh_timeout}"
  ssh_username       = "${var.ssh_username}"
  ssh_password       = "${var.ssh_password}"
  qemuargs           = [
    ["-m", "${var.memory}"],
    ["-smp", "${var.cpus}"],
    ["-cpu", "host"]
  ]
}
