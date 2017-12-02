# StarCraft I (BroodWar) docker images

This repository contains fully working StarCraft
game running in Wine inside of docker image.

It should run on all operating systems (but was tested only on
`Linux 4.10.0-40-generic x86_64`). There might be problems
with docker container networking on Mac/Windows, because
these use virtualization of docker images and has to pass through
special docker gateway.

Specification:

- StarCraft 1.16.1 game from ICCUP (no need for special installs!)
- BWAPI 4.1.2
- BWTA 2.2
- SSCAI maps pack
- 32bit Java
- bwheadless
- wine 2.20.0~xenial
- base image `ubuntu:xenial`

## Usage

Launch an example play of [PurpleWave](https://github.com/dgant/PurpleWave) (P as Protoss) against Tyr (also Protoss) on default map.

    ./run_bots.sh PurpleWave:P Tyr:P

Show help:

    ./run_bots.sh --help

Play against a bot (follow instructions)

    ./play_against_bots.sh PurpleWave:P

Show help:

    ./play_against_bots.sh --help

### Add your own bot

Simply place your java bot to `bots/` directory.

You can see logs from the games in `logs/` directory.

## Dockerhub images

Images are also available on [Dockerhub](https://hub.docker.com/r/ggaic/starcraft/).

You can use:

    ggaic/starcraft:wine
    ggaic/starcraft:bwapi
    ggaic/starcraft:java
    ggaic/starcraft:play

The `run_bots.sh` and `play_against_bots.sh` use docker image `starcraft:play`

## Contributing

PRs are welcome!

Especially from todo list.

### Development

Build images:

    ./build_images.sh

The `run_bots.sh` and `play_against_bots.sh` have special flags `--local`
which will lead to use of local instead of dockerhub images.

## Todo:

- add support for C/C++ bots
- set custom game speed, see how we could integrate bwapi.ini?
- benchmark simulations on top game speed
- add option to launch starcraft game, and bots can connect to it repeatedly
  (save time for repeated plays)
- add some UUID for human games
- add support for singularity containers
- add cached parsed maps: https://github.com/vjurenka/BWMirror/tree/master/bwapi-data/BWTA2
- save replays after game is done into logs folder (or maybe some other one)
- output winner - X vs Y, if Y wins -> output "Y"
- viewing headful via VNC, simplify the process. Maybe use bwapi.ini for hosts?
- sound support (ALSA) :-)

This will go into another repo:

- support "tournament" mode, where a pool of bots can play against each other.
  Calculate ELO ratings.
- Distributed play - pool of workers which will receive info
  about who is to play with whom and they would run the simulation.
  Probably will use RabbitMQ.

## Inspired by

- https://github.com/TorchCraft/TorchCraft/blob/master/docker/no-cuda/Dockerfile
- https://github.com/suchja/x11server/blob/master/Dockerfile
- https://github.com/suchja/wine/blob/master/Dockerfile
- https://hub.docker.com/r/lionax/docker-starcraft/~/dockerfile/

## Some useful links

- https://github.com/TorchCraft/TorchCraft/blob/master/docs/user/bwapi_on_linux.md
- https://github.com/TorchCraft/TorchCraft/blob/master/docs/user/installation.md
- https://github.com/tscmoo/bwheadless/releases
- https://github.com/tscmoo/bwheadless/blob/master/main.cpp#L918
