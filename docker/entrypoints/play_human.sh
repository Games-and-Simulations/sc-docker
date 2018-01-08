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

function FULLY_QUALIFIED_RACE_NAME() {
    SHORT="$1"
    if [ $SHORT == "T" ]; then
        echo "Terran"
    elif [ $SHORT == "P" ]; then
        echo "Protoss"
    elif [ $SHORT == "Z" ]; then
        echo "Zerg"
    elif [ $SHORT == "R" ]; then
        echo "Random"
    fi
}

# Prepare BWAPI version (this copies default bwapi.ini)
cp $BWAPI_DIR/human/* "$BWAPI_DATA_DIR"

cd "$SC_DIR"

# Prepare bwapi.ini
echo "Preparing bwapi.ini"
BWAPI_INI="$BWAPI_DATA_DIR/bwapi.ini"
MAP=$(echo $MAP_NAME | sed "s:$MAP_DIR:maps:g")
RACE=$(FULLY_QUALIFIED_RACE_NAME ${PLAYER_RACE})
DATE=$(date +%Y-%m-%d)
SAVE_REPLAY="maps/replays/xx.rep" #${DATE}_${GAME_NAME}.rep"

# todo: hooks!
sed -i "s:^game = :game = $GAME_NAME:g" "${BWAPI_INI}"
sed -i "s:^character_name = :character_name = $PLAYER_NAME:g" "${BWAPI_INI}"
sed -i "s:^race = :race = $RACE:g" "${BWAPI_INI}"
sed -i "s:^game_type = :game_type = $GAME_TYPE:g" "${BWAPI_INI}"
sed -i "s:^save_replay = :save_replay = $SAVE_REPLAY:g" "${BWAPI_INI}"
sed -i "s:^wait_for_min_players = :wait_for_min_players = $NUM_PLAYERS:g" "${BWAPI_INI}"
sed -i "s:^speed_override = :speed_override = $SPEED_OVERRIDE:g" "${BWAPI_INI}"
cat "$BWAPI_INI"

mv characters/default.spc characters/${PLAYER_NAME}_${NTH_PLAYER}.spc
mv characters/default.mpc characters/${PLAYER_NAME}_${NTH_PLAYER}.mpc

LOG_BASENAME=${GAME_NAME}_${NTH_PLAYER}_${PLAYER_NAME}

# Launch the GUI!
echo "Starting X, savings logs to " "${LOG_DIR}/${LOG_BASENAME}_xvfb.log"
Xvfb :0 -auth ~/.Xauthority -screen 0 640x480x24 >> "${LOG_DIR}/${LOG_BASENAME}_xvfb.log" 2>&1 &
sleep 1

echo "Starting VNC server" ${LOG_DIR}/${LOG_BASENAME}_xvnc.log
x11vnc -forever -nopw -display :0 >> "${LOG_DIR}/${LOG_BASENAME}_xvnc.log" 2>&1 &
sleep 1

# Launch the game!
LOG_GAME="${LOG_DIR}/${LOG_BASENAME}_game.log"
echo "Starting game, savings logs to $LOG_GAME"
echo "------------------------------------------" >> "$LOG_GAME"
echo "Started game at" `date +%Y-%m-%dT%H:%M:%S%z` >> "$LOG_GAME"
launch_game "$@" >> "$LOG_GAME" 2>&1  &

sleep 10

# todo: shutdown the bot & game once it is finished

wait # until bg processes finish
