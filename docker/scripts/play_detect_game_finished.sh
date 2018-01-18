#!/usr/bin/env bash

REPLAY_FILE="$1"

# game is finished if
# - there is a new replay file
# - or the game crashed.

while true
do
    echo "Checking game status ..." >> "$LOG_GAME"

    if ! pgrep -x "StarCraft.exe" > /dev/null
    then
        echo "Game crashed!" >> "$LOG_GAME"
        sleep 3
        exit 1
    fi

    if [ -f "$SC_DIR/$REPLAY_FILE" ] || [ -f "$MAP_DIR/replays/LastReplay.rep" ] ;
    then
        echo "Game finished." >> "$LOG_GAME"
        sleep 3
        exit 0
    fi

    sleep 3
done;
