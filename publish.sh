#!/usr/bin/env bash

docker tag starcraft:wine ggaic/starcraft:wine
docker tag starcraft:bwapi ggaic/starcraft:bwapi
docker tag starcraft:java ggaic/starcraft:java
docker tag starcraft:play ggaic/starcraft:play

docker push ggaic/starcraft:wine
docker push ggaic/starcraft:bwapi
docker push ggaic/starcraft:java
docker push ggaic/starcraft:play

