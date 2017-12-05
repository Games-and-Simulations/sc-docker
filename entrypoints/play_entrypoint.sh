#!/usr/bin/env bash
set -eux

./bwapi_entrypoint.sh

BOT_NAME=$1
GAME_NAME=$2
POSTFIX=$3
shift
shift
shift

# Make sure we have further disambiguation in case same bots play against each other :)
PREFIX="${GAME_NAME}_${POSTFIX}"

# First launch the bot
{
    cd ${BOT_DIR}
    # todo: C-bot
    win_java32 -jar ${BOT_NAME}.jar 2>&1 | tee ${LOG_DIR}/${PREFIX}_bot_${BOT_NAME}.log
} &

sleep 0.5

# if playing against human, don't specify game
# so it can connect easily (bots will discover the game)
if [ "$GAME_NAME" -ne "human_against_bots" ]; then
    GAME="--game ${GAME_NAME}"
else
    GAME=""
fi

# Launch the game!
launch_game \
    --name ${BOT_NAME} \
    ${GAME} \
    "$@" >> ${LOG_DIR}/${PREFIX}_game_${BOT_NAME} 2>&1 &

sleep 10


wait # until bg processes finish

