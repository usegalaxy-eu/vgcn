TeXLive
=========

[![Build Status](https://travis-ci.org/y-yu/ansible-texlive.svg?branch=master)](https://travis-ci.org/y-yu/ansible-texlive)

TeXLive install role for Linux and macOS.

## Install

```
$ ansible-galaxy install y-yu.texlive
```

## Requirements

- Ansible 2.0 or higher
- rsync (if you want to install full)

### Why does the role use rsync?

TeXLive installer (`install-tl`) uses HTTP to pull CTAN packages by default.
But if the installer fails to download, it will start to download over.
Rsync can resume to download, so this role uses rsync if you want to install full packages.

## Role Variables

```yaml
# TeXLive install directory
texlive_directory:
  /usr/local/texlive

# TeXLive mirror
texlive_mirror:
  http://ftp.jaist.ac.jp/pub/CTAN/systems/texlive/tlnet
  
# TeXLive rsync URL
# This is used if you want to install full TeXLive
texlive_rsync:
  rsync://ftp.jaist.ac.jp/pub/CTAN/systems/texlive/tlnet/

# TeXLive Scheme
# full > medium > small > basic
scheme:
  small
```

## Dependencies

None

## Example Playbook

```yaml
- hosts: all
  become: yes
  roles:
    - texlive
```

## License

MIT (See [LICENSE](https://github.com/y-yu/ansible-texlive/blob/master/LICENSE))

## Author Information

Yuu YOSHIMURA
