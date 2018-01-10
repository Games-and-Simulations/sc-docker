#!/usr/bin/env bash
set +x

pushd "/home/starcraft/.wine/drive_c/sc/"

winegui \
    "/home/starcraft/.wine/drive_c/sc/bwheadless.exe" \
    -l "/home/starcraft/.wine/drive_c/sc/bwapi-data/BWAPI.dll" \
    -e "/home/starcraft/.wine/drive_c/sc/StarCraft.exe" \
    --installpath "/home/starcraft/.wine/drive_c/sc/" \
    "$@"

popd
