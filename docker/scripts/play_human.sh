#!/usr/bin/env bash
set -eux

# human is always headful
IS_HEADFUL="1"

LOG_GAME="${LOG_DIR}/game.log"
DATE=$(date +%Y-%m-%d)
REPLAY_FILE="${GAME_NAME}_${NTH_PLAYER}.rep"
BOT_BWAPI="4.2.0"
. play_common.sh

# Prepare BWAPI version (this copies default bwapi.ini)
cp $BWAPI_DIR/human/* "$BWAPI_DATA_DIR"

prepare_bwapi "NULL"
prepare_tm
prepare_character
start_gui
start_game "$@"
sleep 3

if [ "$HEADFUL_AUTO_LAUNCH" == "1" ]; then
    auto_launch
fi

detect_game_finished
LOG "Game finished." >> "$LOG_GAME"
