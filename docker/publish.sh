#!/usr/bin/env bash
set -eux

VERSION=0.1

docker tag starcraft:wine  ggaic/starcraft:wine-$VERSION
docker tag starcraft:bwapi ggaic/starcraft:bwapi-$VERSION
docker tag starcraft:java  ggaic/starcraft:java-$VERSION
docker tag starcraft:play  ggaic/starcraft:play-$VERSION

docker push ggaic/starcraft:wine-$VERSION
docker push ggaic/starcraft:bwapi-$VERSION
docker push ggaic/starcraft:java-$VERSION
docker push ggaic/starcraft:play-$VERSION

