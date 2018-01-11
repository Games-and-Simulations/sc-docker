# Install

What works (has been tested):

  - _Linux / Windows / Mac_: headful/headless play, 1v1 (bot, human), VNC
  - Bot type: `AI_MODULE`, `EXE`, `JAVA_JNI`, `JAVA_MIRROR`
  - Tested on all SSCAIT 2017 tournament bots: _ForceBot, Dawid Loranc, PurpleCheese, Microwave, Blonws31, Lukas Moravec, Hannes Bredberg, Black Crow, TyrProtoss, Arrakhammer, tscmoor, Goliat, Kruecke, NLPRbot, McRave, ZurZurZur, UPStarCraftAI 2016, auxanic, Marine Hell, KaonBot, Neo Edmund Zerg, igjbot, UC3ManoloBot, 100382319, Laura Martin Gallardo, HOLD Z, Pineapple Cactus, MegaBot2017, NiteKatT, Lluvatar, Ecgberht, Korean, FTTankTER, MorglozBot, MadMixP, CherryPi, Guillermo Agitaperas, Hao Pan, WillBot, Niels Justesen, Andrey Kurdiumov, Bryan Weber, AyyyLmao, Yuanheng Zhu, JEMMET, KillAlll, CasiaBot, Steamhammer, Martin Rooijackers, Iron bot, NUS Bot, Roman Danielis, Matej Istenik, Dave Churchill, Tomas Vajda, Marian Devecka, Marek Kadek, Soeren Klett, Jakub Trancik, Oleg Ostroumov, ICELab, Florian Richoux, Andrew Smith, WuliBot, Zia bot, DAIDOES, Flash, Travis Shelton, Bereaver, Aurelien Lermant, AILien, Bjorn P Mattsson, Gaoyuan Chen, Carsten Nielsen, OpprimoBot, PeregrineBot, Sijia Xu, Tomas Cere_

Table of contents:

  * [Docker](#docker)
  * [Python & pip](#python-pip)
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

## Python & pip

TODO: proper python install guide
TODO: create python package
TODO: pip install guide, install package

Lazy version with a lot of sudo:

Ubuntu: http://ubuntuhandbook.org/index.php/2017/07/install-python-3-6-1-in-ubuntu-16-04-lts/
(use `python3.6` instead of just `python`)

    $ curl https://bootstrap.pypa.io/get-pip.py | sudo python3.6

For now, install dependencies using:

    $ pip3.6 install -r requirements.txt

## VNC

Install [RealVNC viewer](https://www.realvnc.com ) for viewing GUI headful modes from the docker images.

Save the executable in PATH so that it can be launched as `vnc-viewer`

## Download maps

Either from http://sscaitournament.com/files/sscai_map_pack.zip
or use `download.sh`
