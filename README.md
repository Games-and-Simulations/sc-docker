# StarCraft I (BroodWar) docker images

`./build_images.sh` to build images.

`./run_bots.sh PurpleWave Tyr` to launch an example play of [PurpleWave](https://github.com/dgant/PurpleWave).

Not finished yet -- only one bot playing now.

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
- two bots playing against each other
- human play against selected bot
- run simulation with winner output - X vs Y, if Y wins -> output Y
