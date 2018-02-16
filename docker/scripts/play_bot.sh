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
REPLAY_FILE="${GAME_NAME}_${NTH_PLAYER}.rep"

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

prepare_tm
prepare_character

if [ "$IS_HEADFUL" == "1" ]; then
    start_gui
fi
start_bot
sleep 1

start_game "$@"
sleep 10

if [ -z "${PLAY_TIMEOUT+set}" ]; then
    detect_game_finished
    LOG "Game finished." >> "$LOG_GAME"
else
    set +e  # run_with_timeout can return non-zero return code
    run_with_timeout "${PLAY_TIMEOUT}" detect_game_finished
    IS_TIMED_OUT=$?
    set -e

    if [ ${IS_TIMED_OUT} -eq 143 ]; then
        LOG "Game realtime outed!" >> "$LOG_GAME"

        # Log ps aux for more info
        LOG "Running processes:"
        ps aux >>  "$LOG_GAME"

        exit EXIT_CODE_REALTIME_OUTED
    else
        LOG "Game finished within realtimeout limit." >> "$LOG_GAME"
    fi
fi

exit 0
