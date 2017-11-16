#!/usr/bin/env bash
set -eux

docker build -f wine.dockerfile -t starcraft:wine .
docker build -f bwapi.dockerfile -t starcraft:bwapi .
docker build -f java.dockerfile -t starcraft:java .

# Some sample java bots
docker build -f purple_bot.dockerfile -t starcraft:purple_bot .
docker build -f tyr_bot.dockerfile -t starcraft:tyr_bot .
