# Install

  * [Docker](#docker)
  * [Python](#python)
  * [VNC viewer](#vnc-viewer)

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

    sudo groupadd docker
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

TODO: test on Mac

## Python

TODO: python install guide

## VNC viewer

Install VNC viewer, for viewing GUI headful modes from the docker images.
We used [TigerVNC](https://github.com/TigerVNC/tigervnc/releases/tag/v1.8.0).
