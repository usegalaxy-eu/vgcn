# Virtual Galaxy Compute Nodes

[Galaxy Europe](https://usegalaxy.eu/) runs jobs on compute nodes belonging
to the
[bwCloud](https://www.bw-cloud.org/)/[de.NBI-cloud](https://www.denbi.de/).
These compute nodes are known as "Virtual Galaxy Compute Nodes" (VGCN).

Virtual Galaxy Compute Nodes boot from VGCN images, which are built off this
repository and made available as
[GitHub releases](https://github.com/usegalaxy-eu/vgcn/releases) and on
[this static site](https://usegalaxy.eu/static/vgcn/).

## Virtual Galaxy Compute Node images

Virtual Galaxy Compute Node images contain everything needed to run
Galaxy jobs.

- [Apptainer](https://apptainer.org/)
- [CVMFS](https://cernvm.cern.ch/fs/)
- [Docker](https://www.docker.com/)
- [NFS](https://nfs.sourceforge.net/)
- [Pulsar](https://github.com/galaxyproject/pulsar)
- [Telegraf](https://www.influxdata.com/time-series-platform/telegraf/)

Each service can be further configured via
[cloud-init](https://cloudinit.readthedocs.io/en/23.2.2/) scripts to meet 
specific needs. A few setup ideas:

- Like on usegalaxy.eu: one machine as the HTCondor master, the rest as job 
  runners.
- Like usegalaxy.eu's remote clusters: one machine as the HTCondor master and
  pulsar server, another as NFS file server, the rest as job runners.
- For "Bring Your own Compute" (BYOC) use cases: A single node that acts as
  HTCondor master, Pulsar server, and job runner.

**Important:** HTCondor has a new authentication mechanism, which uses
passwords and tokens, generated automatically during startup. The easiest and
least error-prone way to set this up is during
[installation](https://htcondor.readthedocs.io/en/latest/getting-htcondor/admin-quick-start.html#administrative-quick-start-guide).

```diff
! This is why we removed HTCondor from public images.
```

You can easily install it and set up your password by adding the `execute`
installation line from the link above to your cloud-init script. There you can
set your own password and host. Both should be identical on all machines you
use, the host is the hostname or IP address of your central manager - usually
the node that accepts Pulsar requests. An implementation in
[Pulsar-Infrastructure-Playbook](https://github.com/usegalaxy-eu/pulsar-infrastructure-playbook)
is in progress.

## Build instructions

Make sure the following packages are installed on your system.

- [Packer](https://www.packer.io/downloads.html) >= 1.9.1, < 2
- [QEMU](https://www.packer.io/downloads.html) >= 6.2, < 9
- [Ansible](https://www.ansible.com/), see [requirements.txt](./requirements.txt)

Run Packer to build the images.

```shell
packer build \
    -only=qemu.rockylinux-8.6-x86_64,qemu.rockylinux-9.2-x86_64 \
    -var="headless=true" \
    -var='groups=["generic", "workers", "external"]' \
    templates
```

- `-only=qemu.rockylinux-8.6-x86_64,qemu.rockylinux-9.2-x86_64`: selects the
  underlying operating system on which the images will be based. One image will
  be produced for each item. The argument can be omitted to produce images for
  all supported operating systems. All builds use the
  [QEMU builder](https://developer.hashicorp.com/packer/integrations/hashicorp/qemu/latest/components/builder/qemu),
  hence the prefix. Supported operating systems are listed in
  [build.pkr.hcl](templates/build.pkr.hcl).
- `-var="headless=true"`: display the screen of the QEMU virtual machines used to build the images by
  setting this variable to false.
- `-var='groups=["generic", "workers", "external"]'`: Playbooks that the Packer
  Ansible provisioner will run. VGCN standard images are built with the setting
  `groups=["generic", "workers", "external"]`. Add `workers-gpu` to the list
  to get the GPU images. Read the comments in 
  [variables.pkr.hcl](templates/variables.pkr.hcl) for more details.
- `templates`: the directory containing the Packer templates.

Once the images are built, they will be available in a new directory called
"images".

## Running VGCN images

Please see [https://github.com/usegalaxy-eu/terraform/](https://github.com/usegalaxy-eu/terraform/) for examples of how to launch and configure this.
