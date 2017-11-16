#!/usr/bin/env bash

wine explorer /desktop=DockerDesktop,1024x768 \
    "/home/starcraft/.wine/drive_c/sc/bwheadless.exe" \
    -l "/home/starcraft/.wine/drive_c/sc/bwapi-data/BWAPI.dll" \
    -e "/home/starcraft/.wine/drive_c/sc/StarCraft.exe" \
    --installpath "/home/starcraft/.wine/drive_c/sc/" \
    --headful &
