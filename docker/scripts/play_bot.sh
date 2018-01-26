#!/usr/bin/env bash
set -eux

if [ "$1" == "--headful" ]; then
    IS_HEADFUL="1"
else
    IS_HEADFUL="0"
fi

LOG_BASENAME="${GAME_NAME}_${NTH_PLAYER}_${PLAYER_NAME//[ ]/_}"
LOG_GAME="${LOG_DIR}/${LOG_BASENAME}_game.log"
LOG_BOT="${LOG_DIR}/${LOG_BASENAME}_bot.log"
BOT_TYPE="${BOT_FILE##*.}"
DATE=$(date +%Y-%m-%d)
REPLAY_FILE="maps/replays/${GAME_NAME}_${NTH_PLAYER}.rep"

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

if [ -z "${PLAY_TIMEOUT+set}" ]; then
    detect_game_finished
    LOG "Game finished." >> "$LOG_GAME"
else
    run_with_timeout "${PLAY_TIMEOUT}" detect_game_finished
    IS_TIMED_OUT=$?
    if [ ${IS_TIMED_OUT} -eq 143 ]; then
        LOG "Game timed out!" >> "$LOG_GAME"

        # Log ps aux for more info
        LOG "Running processes:"
        ps aux >>  "$LOG_GAME"

        exit 1
    else
        LOG "Game finished within timeout limit." >> "$LOG_GAME"
    fi
fi

exit 0
