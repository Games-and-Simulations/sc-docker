#!/usr/bin/env bash
set -eux

./bwapi_entrypoint.sh

BOT_NAME=$1
GAME_NAME=$2
shift
shift # rest of args are passed to launch_game.sh

# Make sure we have further disambiguation in case same bots play against each other :)
RANDOM_POSTFIX=$(cat /proc/sys/kernel/random/uuid)
PREFIX="${GAME_NAME}_${RANDOM_POSTFIX:0:4}"

# First launch the bot
{
    cd ${BOT_DIR}
    # todo: C-bot
    wine ${HOME_DIR}/java/bin/java.exe -jar ${BOT_NAME}.jar 2>&1 | tee ${LOG_DIR}/${PREFIX}_bot_${BOT_NAME}.log
} &

sleep 0.5

# Then launch the game

echo "Launch with $@"
./launch_game.sh \
    --name ${BOT_NAME} \
    --game ${GAME_NAME} \
    "$@" >> ${LOG_DIR}/${PREFIX}_game_${BOT_NAME} 2>&1 &

sleep 10


wait # until bg processes finish

