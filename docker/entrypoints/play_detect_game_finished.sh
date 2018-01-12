#!/usr/bin/env bash

REPLAY_FILE="$1"

# game is finished if
# - there is a new replay file
# - or the game crashed.

while true
do
    echo "Checking game status ..."

    if ! pgrep -x "StarCraft.exe" > /dev/null
    then
        echo "Game crashed!"
        exit 1
    fi

    if [ -f "$SC_DIR/$REPLAY_FILE" ] || [ -f "$MAP_DIR/replays/LastReplay.rep" ] ;
    then
        echo "Game finished."

        [ -f "$MAP_DIR/replays/LastReplay.rep" ] && rm "$MAP_DIR/replays/LastReplay.rep"
        exit 0
    fi

    sleep 3
done;
