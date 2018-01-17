#!/usr/bin/env bash
set -eux

docker build -f dockerfiles/wine.dockerfile  -t starcraft:wine   .
docker build -f dockerfiles/bwapi.dockerfile -t starcraft:bwapi  .
docker build -f dockerfiles/play.dockerfile  -t starcraft:play   .
docker build -f dockerfiles/java.dockerfile  -t starcraft:java   .

pushd ../scbw/local_docker
[ ! -f starcraft.zip ] && curl -SL 'http://files.theabyss.ru/sc/starcraft.zip' -o starcraft.zip
docker build -f game.dockerfile  -t "starcraft:game" .
popd
