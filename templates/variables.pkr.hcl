variable "groups" {
  # Control the playbooks the image is provisioned with.
  /* Using this variable, it is possible to control which playbooks the Ansible
     provisioner will run.

     The Ansible provisioner is configured in "build.pkr.hcl". This variable
     defines the Ansible groups considered during provisioning. To provision an
     image, the Ansible provisioner will run the playbook
     "ansible/all-playbooks.yml", that simply imports all other playbooks in
     the order in which they are expected to be run. Each playbook contains
     plays that only apply to hosts belonging to a group with the same name.

     The end result is that the playbooks with names matching the names defined
     in this variable will be the ones run by the provisioner (but not
     necessarily in the same order).
  */
  type    = list(string)
  default = ["generic"]
}

variable "headless" {
  # Display a window showing the screen of the QEMU virtual machine.
  /* Controls whether a window showing the screen of the virtual machine being
     used to create the image should be displayed.
  */
  type    = string
  default = "true"
}
locals {
  internal = contains(var.groups, "internal")
}
variable "vault_file" {
  type    = string
  default = "--vault-password-file=.vault_password"
}
variable "ansible_extra_args" {
  type = string
  default = ""
}
