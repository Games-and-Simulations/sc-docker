#!/usr/bin/env bash
set -eu

PLAYER_NAME="$1"
PLAYER_RACE="$2"
NTH_PLAYER="$3"
NUM_PLAYERS="$4"
GAME_NAME="$5"
MAP_NAME="$6"
GAME_TYPE="$7"
SPEED_OVERRIDE="$8"
BOT_FILE="$9"
BOT_BWAPI="${10}"
shift 10

LOG_BASENAME=${GAME_NAME}_${NTH_PLAYER}_${PLAYER_NAME}
BOT_TYPE="${BOT_FILE##*.}"
. play_common.sh

# Make sure the bot file exists
if [ ! -f "$BOT_DIR/$BOT_FILE" ]; then
    echo "Bot not found in '$BOT_DIR/$BOT_FILE'"
    exit 1
fi

# Make sure that bot type is recognized
if [ "$BOT_TYPE" != "jar" ] && [ "$BOT_TYPE" != "exe" ] && [ "$BOT_TYPE" != "dll" ]; then
    echo "Bot type can be only one of 'jar', 'exe', 'dll' but the type supplied is '$BOT_TYPE'"
    exit 1
fi

# Copy to BWAPI data dir
cp "$BOT_DIR/$BOT_FILE" "$SC_DIR/$BOT_FILE"

# Prepare BWAPI version (this copies default bwapi.ini)
cp $BWAPI_DIR/$BOT_BWAPI/* "$BWAPI_DATA_DIR"

PREPARE_BWAPI "$BOT_FILE"
PREPARE_CHARACTER
START_GUI
START_BOT
sleep 3

START_GAME "$@"
sleep 10

# todo: shutdown the bot & game once it is finished

wait # until bg processes finish
