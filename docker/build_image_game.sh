#!/usr/bin/env bash

[ ! -f starcraft.zip ] && curl -SL 'http://files.theabyss.ru/sc/starcraft.zip' -o starcraft.zip
docker build -f dockerfiles/game.dockerfile  -t starcraft:game   .
