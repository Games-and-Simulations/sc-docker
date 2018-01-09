# StarCraft I (BroodWar) docker images

This repository contains fully working StarCraft
game running in Wine inside of docker image.

It can launch bots that use BWAPI client to communicate with the game.

## About
We are pleased to publish StarCraft I - BroodWar docker images!

![Starcraft playing on Linux](resources/linux_play.png)

This means the end of complicated game setup for newcomers, or people
who would like to simply play SC1 game against some bot.

You can develop your bots on your favorite platform instead of relying on Windows.

We have more things cooking: It is a part of our ongoing effort to create environment for reinforcement learning bots
(bots that improve through self-play).

This project is maintained by [Games and Simulations group](http://gas.fel.cvut.cz/)
which is also behind [student starcraft AI tournament](http://sscaitournament.com).


![Patreon](resources/patreon.png)

If you'd like to [support us on Patreon](https://www.patreon.com/sscait), we would be very grateful!


## Install

See [installation instructions for Linux / Windows / Mac](INSTALL.md).

It should run well on new versions of major operating systems. It was tested on:

- Ubuntu 17.04 Zesty, `Linux 4.10.0-40-generic x86_64`
- Microsoft Windows 10 (64-bit)
- Mac OS Sieria 10.12.6 (64-bit, Mac mini)

(testing and reporting on other platforms is very welcome, especially Mac!)

## Usage

Launch a headless play of [PurpleWave](https://github.com/dgant/PurpleWave) (P as Protoss) against Example Bot on default map.

    $ ./run_bots.sh ExampleBot:T PurpleWave:P
    f463e69d-7bbd-4638-a9a4

See [more usage examples](USAGE.md).

## Known limitations

- Running .dll works only in headful mode, not in headless. 
  Please compile as .exe and it will work. 

## Specification

- StarCraft 1.16.1 game from ICCUP (no need for special installs!)
- BWAPI 4.1.2
- BWTA 2.2
- SSCAI maps pack
- 32bit oracle Java 8 `1.8.0_152-b16`
- bwheadless `v0.1`
- wine `2.20.0~xenial`
- base image `ubuntu:xenial`


## Dockerhub images

Images are also available on [Dockerhub](https://hub.docker.com/r/ggaic/starcraft/).

You can use:

    ggaic/starcraft:wine
    ggaic/starcraft:bwapi
    ggaic/starcraft:java
    ggaic/starcraft:play

These are latest stable images and are subject to change.

You can use [stable images with version postfix, which correspond to git tags](https://hub.docker.com/r/ggaic/starcraft/tags/).

## Contributing

Pull requests are welcome! There are still many things to do, especially from [todo list](TODO.md).

## Citation

If you use `sc-docker` in your (academic) work, please cite us:

    @misc{StarcraftDocker,
      title = {Multi-platform Version of StarCraft: Brood War in a Docker Container: Technical Report},
      author = "Sustr, Michal and Maly, Jan and Certicky, Michal",
      howpublished = {\url{https://arxiv.org/abs/1801.02193}},
    }

## Links

Inspired by

- https://github.com/TorchCraft/TorchCraft/blob/master/docker/no-cuda/Dockerfile
- https://github.com/suchja/x11server/blob/master/Dockerfile
- https://github.com/suchja/wine/blob/master/Dockerfile
- https://hub.docker.com/r/lionax/docker-starcraft/~/dockerfile/

Some useful links

- https://github.com/TorchCraft/TorchCraft/blob/master/docs/user/bwapi_on_linux.md
- https://github.com/TorchCraft/TorchCraft/blob/master/docs/user/installation.md
- https://github.com/tscmoo/bwheadless/releases
- https://github.com/tscmoo/bwheadless/blob/master/main.cpp#L918
