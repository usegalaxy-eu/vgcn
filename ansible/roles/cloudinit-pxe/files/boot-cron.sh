#!/bin/bash

# Create user if it doesn't exist
if ! id "centos" &>/dev/null; then
    useradd -m -c "RHEL Cloud User" -s /bin/bash centos
fi

# Ensure user is part of specified groups
usermod -aG wheel,adm,systemd-journal centos

# Set up passwordless sudo
echo "centos ALL=(ALL) NOPASSWD:ALL" >/etc/sudoers.d/90-cloud-init-centos
chmod 440 /etc/sudoers.d/90-cloud-init-centos

sed -i 's|nameserver 10.0.2.3||g' /etc/resolv.conf
sed -i "s|localhost.localdomain|$(hostname -f)|g" /etc/telegraf/telegraf.conf
ssh-keygen -s /tmp/server_ca -I key_for_test1 -h -V +52w /etc/ssh/ssh_host_rsa_key.pub
ssh-keygen -s /tmp/server_ca -I key_for_test1 -h -V +52w /etc/ssh/ssh_host_ecdsa_key.pub
ssh-keygen -s /tmp/server_ca -I key_for_test1 -h -V +52w /etc/ssh/ssh_host_ed25519_key.pub
rm -f /tmp/server_ca
systemctl restart sshd
systemctl restart condor
systemctl restart telegraf
systemctl restart docker
