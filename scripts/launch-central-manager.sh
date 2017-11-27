
#!/bin/sh

IMAGE=vgcocm7-14
FLAVOR=m1.medium
SSHKEY=cloud2
AZONE=Service-Environment
NETWORK=868ad51a-fc5c-416b-883e-97fca84f1d2c
IPADDR=10.19.0.16

nova boot \
        --image $IMAGE \
        --flavor $FLAVOR \
        --key-name $SSHKEY \
        --availability-zone $AZONE \
        --nic net-id=${NETWORK},v4-fixed-ip=${IPADDR} \
        vgcocm
