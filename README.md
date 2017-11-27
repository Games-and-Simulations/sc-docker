# StarCraft I (BroodWar) docker images

Build images:

    ./build_images.sh

Launch an example play of [PurpleWave](https://github.com/dgant/PurpleWave) (P as Protoss) against Tyr (also Protoss) on default map.

    ./run_bots.sh PurpleWave:P Tyr:P

Show help:

    ./run_bots.sh --help

Play against a bot (follow instructions)

    ./play_against_bots.sh PurpleWave:P


## Inspired by

- https://github.com/TorchCraft/TorchCraft/blob/master/docker/no-cuda/Dockerfile
- https://github.com/suchja/x11server/blob/master/Dockerfile
- https://github.com/suchja/wine/blob/master/Dockerfile
- https://hub.docker.com/r/lionax/docker-starcraft/~/dockerfile/

## Some useful links:

- https://github.com/TorchCraft/TorchCraft/blob/master/docs/user/bwapi_on_linux.md
- https://github.com/TorchCraft/TorchCraft/blob/master/docs/user/installation.md
- https://github.com/tscmoo/bwheadless/releases
- https://github.com/tscmoo/bwheadless/blob/master/main.cpp#L918

## Todo:

- parsed replays: https://github.com/vjurenka/BWMirror/tree/master/bwapi-data/BWTA2
- headless/headful modes
- run simulation with winner output - X vs Y, if Y wins -> output Y
