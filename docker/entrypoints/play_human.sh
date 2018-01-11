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

# human is always headful
IS_HEADFUL="1"

LOG_BASENAME=${GAME_NAME}_${NTH_PLAYER}_${PLAYER_NAME}
DATE=$(date +%Y-%m-%d)
REPLAY_FILE="maps/replays/${DATE}_${GAME_NAME}_${NTH_PLAYER}.rep"
. play_common.sh

# Prepare BWAPI version (this copies default bwapi.ini)
cp $BWAPI_DIR/human/* "$BWAPI_DATA_DIR"

prepare_bwapi "NULL"
prepare_character
start_gui
start_game "$@"
sleep 10

detect_game_finished
