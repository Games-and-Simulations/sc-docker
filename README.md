# StarCraft I (BroodWar) docker images

Build images:

    ./build_images.sh

Launch an example play of [PurpleWave](https://github.com/dgant/PurpleWave) (P as Protoss) against Tyr (also Protoss) on default map.

    ./run_bots.sh PurpleWave:P Tyr:P

Show help:

    ./run_bots.sh --help

Play against a bot (follow instructions)

    ./play_against_bots.sh PurpleWave:P

Show help:

    ./play_against_bots.sh --help


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
