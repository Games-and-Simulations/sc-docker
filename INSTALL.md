# Install

What works (has been tested):

  - Linux: headful/headless play, 1v1 (bot, human), VNC
  - Windows: headless play, 1v1 (bot, human), _headful only via VNC_
  - Mac: headless play, 1v1 (bot, human), _headful only via VNC_
    (Headful natively could work if X server is installed - [if you try, please let us know](https://forums.docker.com/t/how-to-run-gui-apps-in-containiers-in-osx-docker-for-mac/17797/15).)

Table of contents:

  * [Docker](#docker)
  * [Python](#python)
  * [Pip](#pip)
  * [VNC viewer - optional](#vnc)

## Docker

Docker version used to build the images is `17.09.0-ce`

### Ubuntu

Based on https://docs.docker.com/engine/installation/linux/docker-ce/ubuntu/

Copy-paste script into terminal:

    sudo apt-get update
    sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
    # add docker repository
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    # install docker
    sudo apt-get update
    sudo apt install -y docker-ce=17.09.0~ce-0~ubuntu
    # Make sure you can run docker without sudo
    # (based on https://docs.docker.com/engine/installation/linux/linux-postinstall/#manage-docker-as-a-non-root-user)
    sudo usermod -aG docker $USER
    # Log out and log back in so that your group membership is re-evaluated.
    # (close and open terminal window)


Test to check install was successful:

    docker run hello-world

You can manually [download docker of specified version](https://download.docker.com) if it is missing from list of packages. For example

- [Ubuntu 17.04 Zesty 64-bit `docker-ce` package](https://download.docker.com/linux/ubuntu/dists/zesty/pool/stable/amd64/docker-ce_17.09.0~ce-0~ubuntu_amd64.deb)

### Windows

You may want to [read through manual for installing docker on Windows](https://docs.docker.com/docker-for-windows/install/)
for troubleshooting.

- Go to [docker releases for Windows](https://docs.docker.com/docker-for-windows/release-notes/#docker-community-edition-17090-ce-win32-2017-10-02-stable)
  and download `Docker Community Edition 17.09.0-ce-win33 2017-10-06 (Stable)` ([direct download link](https://download.docker.com/win/stable/13620/Docker%20for%20Windows%20Installer.exe))
- Follow install instructions.

You may need to turn on virtualization support for your CPU (in BIOS).

Test in power shell to check install was successful:

    docker run hello-world

### Mac

You may want to [read through manual for installing docker on Mac](https://docs.docker.com/docker-for-mac/install/)
for troubleshooting.

- Go to [docker releases for Mac](https://docs.docker.com/docker-for-mac/release-notes/#docker-community-edition-17090-ce-mac33-2017-10-03-stable)
  and download `Docker Community Edition 17.09.0-ce-mac33 2017-10-03 (Stable)` ([direct download link](https://download.docker.com/mac/stable/19543/Docker.dmg))
- Follow install instructions.

Test in terminal that install was successful:

    docker run hello-world

## Python

TODO: python install guide

## Pip

TODO: pip install guide, install package

## VNC

Install VNC viewer, for viewing GUI headful modes from the docker images.
We used [TigerVNC](https://github.com/TigerVNC/tigervnc/releases/tag/v1.8.0).
