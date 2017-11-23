#!/usr/bin/env bash
set -eux


docker build -f dockerfiles/wine.dockerfile   -t starcraft:wine   .
docker build -f dockerfiles/bwapi.dockerfile  -t starcraft:bwapi  .
docker build -f dockerfiles/java.dockerfile   -t starcraft:java   .

