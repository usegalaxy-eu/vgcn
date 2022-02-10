# Virtual Galaxy Compute Nodes (VGCN)

This repo contains all of the components required to build the "Virtual Galaxy
Compute Nodes" (VGCN) that make up the HTCondor cloud used in UseGalaxy.eu

Pre-built images are available here: [https://usegalaxy.eu/static/vgcn/](https://usegalaxy.eu/static/vgcn/)

## Features

All in one image, a single image gets you:

- HTCondor
- Pulsar
- NFS
- CVMFS
- Singularity
- Docker

Everything you need to run Galaxy jobs. You can structure this in various ways that meet your needs:

- Like useGalaxy.eu: one VM as the condor master, another N as job runners
- Like EU's remote clusters: one VM as the condor master + pulsar, another as NFS, and the rest as job runners
- For BYOC: A single node that does condor master + pulsar + job execution

## Development
Development happens into the __dev__ branch, images are built from __main__ branch.

## Changelog

- 50:
    - MODIFIED: updated Pulsar to version 0.14.11
    - MODIFIED: moved to kernel 5.x
- 40:
    - ADDED: Nvidia driver
    - ADDED: Cuda toolkit
    - ADDED: GPU accelerated Docker containers support
    - MODIFIED: moved to CENTOS8
    - MODIFIED: updated Pulsar to version 0.14.0
    - MODIFIED: updated HTCondor to version 8.8
- 32:
    - MODIFIED: Pulsar toward Py3
- 31:
    - ADDED: Pulsar
    - ADDED: Fonts for some jobs
    - ADDED: `at` daemon
    - MODIFIED: Additional 'internal' and 'external' targets allowing us to include signed SSH host keys.
    - REMOVED: vault
    - REMOVED: roced
- 21: Initial Release

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
