#!/usr/bin/env bash
set -eux

./bwapi_entrypoint.sh

BOT_1=$1
BOT_2=$2

files=($BOT_DIR)
if [ ${#files[@]} -eq 0 ]; then
    echo "No bot files have been provided! Exitting..."
    exit 1
fi

# Prepare bot directory - add links to folders it might need
#ln -s ${BWTA_DIR} ${BOT_DIR}

# First launch the bot
pushd ${BOT_DIR}
wine ${HOME_DIR}/java/bin/java.exe -jar ${BOT_1}.jar 2>&1 | tee ${LOG_DIR}/bot_${BOT_1}.log &
# todo: two bots
# wine ${HOME_DIR}/java/bin/java.exe -jar ${BOT_2}.jar 2>&1 | tee ${LOG_DIR}/bot_${BOT_2}.log &
popd

sleep 0.5

# Then launch the game
./launch_game.sh --headful >> ${LOG_DIR}/game 2>&1 &

wait
