#!/usr/bin/env bash
set -eux

BUILD_ARGS="--build-arg BOT_UID=${BOT_UID:-1000} --build-arg STARCRAFT_UID=${STARCRAFT_UID:-1001}"

docker build ${BUILD_ARGS} -f dockerfiles/wine.dockerfile  -t starcraft:wine   .
docker build ${BUILD_ARGS} -f dockerfiles/bwapi.dockerfile -t starcraft:bwapi  .
docker build ${BUILD_ARGS} -f dockerfiles/play.dockerfile  -t starcraft:play   .
docker build ${BUILD_ARGS} -f dockerfiles/java.dockerfile  -t starcraft:java   .

pushd ../scbw/local_docker
[ ! -f starcraft.zip ] && curl -SL 'http://files.theabyss.ru/sc/starcraft.zip' -o starcraft.zip
docker build ${BUILD_ARGS} -f game.dockerfile  -t "starcraft:game" .
popd
