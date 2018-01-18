#!/usr/bin/env bash
set -eux

# human is always headful
IS_HEADFUL="1"

LOG_BASENAME=${GAME_NAME}_${NTH_PLAYER}_${PLAYER_NAME}
LOG_GAME="${LOG_DIR}/${LOG_BASENAME}_game.log"
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

./play_detect_game_finished.sh "$REPLAY_FILE"
echo "Game finished." >> "$LOG_GAME"
