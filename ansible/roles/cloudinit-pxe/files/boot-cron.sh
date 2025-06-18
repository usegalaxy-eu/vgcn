#!/bin/bash

if [ -e /etc/init_success ]; then
    exit 0
fi
# Create user if it doesn't exist
if ! id "centos" &>/dev/null; then
    useradd -m -c "RHEL Cloud User" -s /bin/bash centos
fi

# Create scratch storage for PXE machines
SCRATCH_DEVICE=/dev/mapper/tank
SCRATCH_MOUNT=/scratch
if [ -e /opt/openslx ]; then
    if ! blkid "$SCRATCH_DEVICE" 2>/dev/null | grep -q 'TYPE="xfs"' ; then
        if grep -qs "$SCRATCH_MOUNT " /proc/mounts; then
            systemctl stop docker
            sleep 2
            umount "$SCRATCH_MOUNT"
        fi
        mkfs.xfs -f "$SCRATCH_DEVICE"
    fi
    if ! grep -qs "$SCRATCH_MOUNT " /proc/mounts; then
        mount "$SCRATCH_DEVICE" "$SCRATCH_MOUNT"
    fi
fi

# Change GalaxyGroup based on nvidia detection
if nvidia-smi &> /dev/null; then
    sed -i 's/.*GalaxyGroup = "training-pxe-test".*/GalaxyGroup = "training-pxe-test-gpu"/' /etc/condor/config.d/99-cloud-init.conf
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

touch /etc/init_success
