# Virtual Galaxy Compute Nodes (VGCN)

This repo contains all of the components required to build the "Virtual Galaxy
Compute Nodes" (VGCN) that make up the HTCondor cloud used in UseGalaxy.eu

Pre-built images are available here: [https://usegalaxy.eu/static/vgcn/](https://usegalaxy.eu/static/vgcn/)

## Features

All in one image, a single image gets you:

- Pulsar
- NFS
- CVMFS
- Apptainer (former Singularity)
- Docker
- Telegraf

Everything you need to run Galaxy jobs. You can structure this in various ways that meet your needs:

- Like useGalaxy.eu: one VM as the condor master, another N as job runners
- Like EU's remote clusters: one VM as the condor master + pulsar, another as NFS, and the rest as job runners
- For BYOC: A single node that does condor master + pulsar + job execution

**Important:** HTCondor has a new authentication mechanism, which uses passwords and tokens, generated automatically during startup. The easiest and least error-prone way to set this up is during [installation](https://htcondor.readthedocs.io/en/latest/getting-htcondor/admin-quick-start.html#administrative-quick-start-guide).  
```diff
! This is why we removed HTCondor from public images.
```
You can easily install it and set up your password by adding the `execute` installation line from the link above to your cloud-init script. There you can set your own password and host. Both should be identical on all machines you use, the host is the hostname or IP address of your central manager - usually the node that accepts Pulsar requests. An implementation in [Pulsar-Infrastructure-Playbook](https://github.com/usegalaxy-eu/pulsar-infrastructure-playbook) is in progress.
## Development

Development happens into the __dev__ branch, images are built from __main__ branch.

## Changelog

- 70:
    - ADDED: FS limit for condor.service (250GB soft, 1 TB hard)
    - ADDED: UID and GID 999 will be remapped to make it available for galaxy (updated handy_os role)
    - REMOVED: HTCondor removed from public images (see for reason above)
    - REMOVED: CentOS 7 support
    - MODIFIED: moved to Rocky Linux 9
    - MODIFIED: SELinux on permissive by default; the secure target bacame obsolete
    - MODIFIED: updated Telegraf to version 1.18.2
    - MODIFIED: Singularity is now Apptainer
    - MODIFIED: Bumped Ansible to version 6.7.0
- 60:
    - MODIFIED: moved to Rocky Linux 8
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
        centos-8.x-x86_64/base
        rockylinux-8.x-x86_64/base
        rockylinux-9.x-x86_64/base

Provisioning:
        centos-8.x-x86_64/vgcn-bwcloud
        centos-8.x-x86_64/vgcn-bwcloud-gpu
        centos-8.x-x86_64/jenkins
        centos-8.x-x86_64/generic
        rockylinux-8.x-x86_64/vgcn-bwcloud
        rockylinux-8.x-x86_64/vgcn-bwcloud-gpu
        rockylinux-8.x-x86_64/jenkins
        rockylinux-8.x-x86_64/generic
        rockylinux-9.x-x86_64/vgcn-bwcloud
        rockylinux-9.x-x86_64/vgcn-bwcloud-gpu
        rockylinux-9.x-x86_64/jenkins
        rockylinux-9.x-x86_64/generic
```
To build the VGCN-bwcloud Image with Rocky 9, execute the following steps:
```bash
make rockylinux-9.x-x86_64/base
make rockylinux-9.x-x86_64/vgcn-bwcloud
make rockylinux-9.x-x86_64/vgcn-bwcloud-external
```
```diff
! Please make sure to build the rockylinux-9.x-86_64/vgcn-bwcloud(-gpu)-external as last step. The image does not work as expected otherwise.
```
## Dependencies

We have listed the versions we use, but other versions may work.

| Component                                      | Version    |
|------------------------------------------------|------------|
| [Packer](https://www.packer.io/downloads.html) | 1.8.5      |
| Ansible (Community version number)             | >= 6.7.0   |
| qemu                                           | 7.0.0      |

## Building This Yourself
Create a python virtual environment using python >= 3.9 and install the requirements.txt
This ensures you get the correct ansible and packer version, because some commands might fail otherwise.

All of the images are designed to be as generic as possible so you can use them
as-is. We will provide built images, but if you wish to build them yourself,
you'll simply want to do:

```
make rockylinux-8.x-x86_64/vgcn-bwcloud
```

## Running It

Please see https://github.com/usegalaxy-eu/terraform/ for examples of how to launch and configure this.
