#!/usr/bin/env bash


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

function PREPARE_BWAPI() {
    PLAYER="$1"

    echo "Preparing bwapi.ini"
    BWAPI_INI="$BWAPI_DATA_DIR/bwapi.ini"

    MAP=$(echo $MAP_NAME | sed "s:$MAP_DIR:maps:g")
    RACE=$(FULLY_QUALIFIED_RACE_NAME ${PLAYER_RACE})
    DATE=$(date +%Y-%m-%d)
    SAVE_REPLAY="maps/replays/xx.rep" #${DATE}_${GAME_NAME}.rep"

    # todo: AI MODULE!
    #sed -i "s:^ai = NULL:ai = $PLAYER:g" "${BWAPI_INI}"
    sed -i "s:^game = :game = $GAME_NAME:g" "${BWAPI_INI}"
    sed -i "s:^character_name = :character_name = $PLAYER_NAME:g" "${BWAPI_INI}"
    sed -i "s:^race = :race = $RACE:g" "${BWAPI_INI}"
    sed -i "s:^game_type = :game_type = $GAME_TYPE:g" "${BWAPI_INI}"
    sed -i "s:^save_replay = :save_replay = $SAVE_REPLAY:g" "${BWAPI_INI}"
    sed -i "s:^wait_for_min_players = :wait_for_min_players = $NUM_PLAYERS:g" "${BWAPI_INI}"
    sed -i "s:^speed_override = :speed_override = $SPEED_OVERRIDE:g" "${BWAPI_INI}"

    # todo: solve bug with "Unable to distribute map"
    #if [ $NTH_PLAYER == "0" ]; then # if is_server
    #    sed -i "s:map = :map = $MAP:g" "${BWAPI_INI}"
    #fi

    . hook_update_bwapi_ini.sh

    cat "$BWAPI_INI"
}

function START_GUI() {
    # Launch the GUI!
    echo "Starting X, savings logs to " "${LOG_DIR}/${LOG_BASENAME}_xvfb.log"
    Xvfb :0 -auth ~/.Xauthority -screen 0 640x480x24 >> "${LOG_DIR}/${LOG_BASENAME}_xvfb.log" 2>&1 &
    sleep 1

    echo "Starting VNC server" ${LOG_DIR}/${LOG_BASENAME}_xvnc.log
    x11vnc -forever -nopw -display :0 >> "${LOG_DIR}/${LOG_BASENAME}_xvnc.log" 2>&1 &
    sleep 1
}

function START_BOT() {
    . hook_before_bot_start.sh

    # Launch the bot!
    LOG_BOT="${LOG_DIR}/${LOG_BASENAME}_bot.log"
    echo "Starting bot ${BOT_FILE}, savings logs to $LOG_BOT"
    echo "------------------------------------------" >> "$LOG_BOT"
    echo "Started bot at" `date +%Y-%m-%dT%H:%M:%S%z` >> "$LOG_BOT"
    {
        pushd $SC_DIR

        # todo: run under "bot"
        if [ "$BOT_TYPE" == "jar" ]; then
            win_java32 -jar ${BOT_FILE} >> "${LOG_DIR}/${LOG_BASENAME}_bot.log" 2>&1
        elif [ "$BOT_TYPE" == "exe" ]; then
            wine ${BOT_FILE} >> "${LOG_DIR}/${LOG_BASENAME}_bot.log" 2>&1
        fi

        popd
    } &

    . hook_after_bot_start.sh

}

function START_GAME() {
    . hook_before_game_start.sh

    # Launch the game!
    LOG_GAME="${LOG_DIR}/${LOG_BASENAME}_game.log"
    echo "Starting game, savings logs to $LOG_GAME"
    echo "------------------------------------------" >> "$LOG_GAME"
    echo "Started game at" `date +%Y-%m-%dT%H:%M:%S%z` >> "$LOG_GAME"
    launch_game "$@" >> "$LOG_GAME" 2>&1  &

    . hook_after_game_start.sh
}

function PREPARE_CHARACTER() {
    mv $SC_DIR/characters/default.spc $SC_DIR/characters/${PLAYER_NAME}_${NTH_PLAYER}.spc
    mv $SC_DIR/characters/default.mpc $SC_DIR/characters/${PLAYER_NAME}_${NTH_PLAYER}.mpc
}
