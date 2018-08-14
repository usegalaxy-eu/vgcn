# Virtual Galaxy Compute Nodes

This repo contains all of the components required to build the "Virtual Galaxy
Compute Nodes" (VGCN) that make up the HTCondor cloud used in UseGalaxy.eu

## Makefile

We include a makefile that should build the images, running `make` will inform you of the available targets:

```console
$ make
General syntax: <template>/<flavor>[/boot]
Detected builders:
        qemu
Base images:
        centos-7.x-x86_64/base
Provisioning:
        centos-7.x-x86_64/vgcn-bwcloud
        centos-7.x-x86_64/jenkins
```

## Dependencies

We have listed the versions we use, but other versions may work.

Component                                      | Version
---------------------------------------------- | --------
[Packer](https://www.packer.io/downloads.html) | 1.0.4
Ansible                                        | >= 2.4.3.0
qemu                                           | 2.5.0

## Building This Yourself

All of the images are designed to be as generic as possible so you can use them
as-is. We will provide built images, but if you wish to build them yourself,
you'll simply want to do:

```
make centos-7.x-x86_64/vgcn-bwcloud
```

## Running It

Please see https://github.com/usegalaxy-eu/terraform/ for examples of how to launch and configure this.
