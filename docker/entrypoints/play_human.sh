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
shift 8

LOG_BASENAME=${GAME_NAME}_${NTH_PLAYER}_${PLAYER_NAME}
. play_common.sh

# Prepare BWAPI version (this copies default bwapi.ini)
cp $BWAPI_DIR/human/* "$BWAPI_DATA_DIR"

PREPARE_BWAPI "NULL"
PREPARE_CHARACTER
START_GUI
START_GAME "$@"
sleep 10

# todo: shutdown the bot & game once it is finished

wait # until bg processes finish
