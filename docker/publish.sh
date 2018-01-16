#!/usr/bin/env bash
set -eux

# do not publish starcraft:game
VERSION=$(python ../setup.py --version)

docker tag starcraft:wine  ggaic/starcraft:wine
docker tag starcraft:bwapi ggaic/starcraft:bwapi
docker tag starcraft:java  ggaic/starcraft:java
docker tag starcraft:play  ggaic/starcraft:play
docker tag starcraft:wine  ggaic/starcraft:wine-${VERSION}
docker tag starcraft:bwapi ggaic/starcraft:bwapi-${VERSION}
docker tag starcraft:java  ggaic/starcraft:java-${VERSION}
docker tag starcraft:play  ggaic/starcraft:play-${VERSION}

docker push ggaic/starcraft:wine
docker push ggaic/starcraft:bwapi
docker push ggaic/starcraft:java
docker push ggaic/starcraft:play
docker push ggaic/starcraft:wine-${VERSION}
docker push ggaic/starcraft:bwapi-${VERSION}
docker push ggaic/starcraft:java-${VERSION}
docker push ggaic/starcraft:play-${VERSION}
