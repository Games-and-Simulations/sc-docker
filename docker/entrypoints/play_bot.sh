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
BOT_NAME="$9"
BOT_FILE="${10}"
shift 10

if [ "$1" == "--headful" ]; then
    IS_HEADFUL="1"
else
    IS_HEADFUL="0"
fi

LOG_BASENAME="${GAME_NAME}_${NTH_PLAYER}_${PLAYER_NAME}"
BOT_TYPE="${BOT_FILE##*.}"
DATE=$(date +%Y-%m-%d)
REPLAY_FILE="maps/replays/${DATE}_${GAME_NAME}_${NTH_PLAYER}.rep"

. play_common.sh

check_bot_requirements

# Copy to BWAPI data dir
cp -r "$BOT_DIR/$BOT_NAME/AI/." "$BOT_DATA_AI_DIR"
cp -r "$BOT_DIR/$BOT_NAME/read/." "$BOT_DATA_READ_DIR"
cp -r "$BWAPI_DIR/bot/." "$BWAPI_DATA_DIR"
cp "$BOT_DIR/$BOT_NAME/BWAPI.dll" "$BWAPI_DATA_DIR"


BOT_EXECUTABLE="$BWAPI_DATA_DIR/AI/$BOT_FILE"
if [ "$BOT_TYPE" == "dll" ]; then
    prepare_bwapi "bwapi-data/AI/$BOT_FILE"
else
    prepare_bwapi "NULL"
fi

prepare_character
start_gui
start_bot
sleep 3

start_game "$@"
sleep 10

detect_game_finished
