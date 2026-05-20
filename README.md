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

Run the `build.py` script to automatically template, provision, and assemble the image. 

```shell
python build.py <template> <provisioning>... <delivery> [options]
```

**Example:**
```shell
python build.py rockylinux-10-latest-x86_64 workers internal cloud -q
```

### Arguments

- **`template`**: Selects the underlying operating system on which the image will be based. Supported templates can be found as `source.qemu.*` blocks in `templates/build.pkr.hcl` (e.g., `rockylinux-10-latest-x86_64`, `rockylinux-9-latest-x86_64`).
- **`provisioning`**: One or more Ansible playbooks to run (e.g., `workers`, `internal`, `jenkins`). Note that the `generic` playbook is implicit and applied globally to all builds.
- **`delivery`**: The delivery method or destination environment, which dictates the cloud-init and boot structure. This argument expects exactly one of the mutually exclusive choices: `cloud`, `kvm`, or `pxe` (use `no` to omit all). For local development this argument should default to `no`.

### Options

- `--openstack`: Automatically convert and upload the built image to your OpenStack tenant. Ensure your OpenStack RC file credentials are sourced.
- `--conda-env <path>`: Specifies a conda environment path containing `packer` and `qemu-img` binaries.
- `--publish <key_path>`: Secure copy the resulting raw image to the static hosting site and adjust permissions.
- `--dry-run`: Output the generated Packer and shell commands without executing them.
- `-q`, `--quiet`: Supress the spinner output during build.

Once the images are built and converted, a `.raw` output file will be available in the root directory.

## Running VGCN images

Please see [https://github.com/usegalaxy-eu/terraform/](https://github.com/usegalaxy-eu/terraform/) for examples of how to launch and configure this.
