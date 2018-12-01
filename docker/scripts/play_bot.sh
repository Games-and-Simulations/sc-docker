#!/usr/bin/env bash
set -eux

if [ "$1" == "--headful" ]; then
    IS_HEADFUL="1"
else
    IS_HEADFUL="0"
fi

LOG_GAME="${LOG_DIR}/game.log"
LOG_BOT="${LOG_DIR}/bot.log"
BOT_TYPE="${BOT_FILE##*.}"
DATE=$(date +%Y-%m-%d)
REPLAY_FILE="${GAME_NAME}_${NTH_PLAYER}.rep"

. play_common.sh

check_bot_requirements

# Copy to BWAPI data dir
cp -r "$BOT_DIR/AI/." "$BOT_DATA_AI_DIR"
cp -r "$BOT_DIR/supplementalAI/." "$BOT_DATA_AI_DIR" || true
cp -r "$BOT_DIR/read/." "$BOT_DATA_READ_DIR"
cp -r "$BOT_DIR/supplementalRead/." "$BOT_DATA_READ_DIR" || true
cp "$BOT_DIR/BWAPI.dll" "$BWAPI_DATA_DIR"
cp -r "$BWAPI_DIR/bot/." "$BWAPI_DATA_DIR"


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
sleep 3

connect_bot
sleep 1

if [ "$IS_HEADFUL" == "1" ] && [ $NTH_PLAYER == "0" ] && [ "$HEADFUL_AUTO_LAUNCH" == "1" ]; then # if is_server
    auto_launch
fi

if [ "$CAPTURE_MOUSE_MOVEMENT" == "1" ]; then
    /app/play_capture_mouse_movement.sh &
fi


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
