#!/usr/bin/env bash


function fully_qualified_race_name() {
    SHORT="$1"
    if [ "$SHORT" == "T" ]; then
        echo "Terran"
    elif [ "$SHORT" == "P" ]; then
        echo "Protoss"
    elif [ "$SHORT" == "Z" ]; then
        echo "Zerg"
    elif [ "$SHORT" == "R" ]; then
        echo "Random"
    fi
}

function prepare_bwapi() {
    PLAYER="$1"

    echo "Preparing bwapi.ini"
    BWAPI_INI="$BWAPI_DATA_DIR/bwapi.ini"

    MAP=$(echo $MAP_NAME | sed "s:$MAP_DIR:maps:g")
    RACE=$(fully_qualified_race_name ${PLAYER_RACE})
    DATE=$(date +%Y-%m-%d)
    SAVE_REPLAY="maps/replays/${DATE}_${GAME_NAME}.rep"

    sed -i "s:^ai = NULL:ai = $PLAYER:g" "${BWAPI_INI}"
    sed -i "s:^character_name = :character_name = $PLAYER_NAME:g" "${BWAPI_INI}"
    sed -i "s:^race = :race = $RACE:g" "${BWAPI_INI}"
    sed -i "s:^game_type = :game_type = $GAME_TYPE:g" "${BWAPI_INI}"
    sed -i "s:^save_replay = :save_replay = $SAVE_REPLAY:g" "${BWAPI_INI}"
    sed -i "s:^wait_for_min_players = :wait_for_min_players = $NUM_PLAYERS:g" "${BWAPI_INI}"
    sed -i "s:^speed_override = :speed_override = $SPEED_OVERRIDE:g" "${BWAPI_INI}"

    # todo: solve bug with "Unable to distribute map"
    # hotfix for headful mode, but we need to select map unfortunately
    # it works for headless mode
    if [ "$IS_HEADFUL" == "1" ]; then
        sed -i "s:^game = :game = JOIN_FIRST:g" "${BWAPI_INI}"
    else
        if [ $NTH_PLAYER == "0" ]; then # if is_server
            sed -i "s:map = :map = $MAP:g" "${BWAPI_INI}"
        fi
        sed -i "s:^game = :game = ${GAME_NAME}:g" "${BWAPI_INI}"
    fi

    . hook_update_bwapi_ini.sh

    cat "$BWAPI_INI"
}

function start_gui() {
    # Launch the GUI!
    echo "Starting X, savings logs to " "${LOG_DIR}/${LOG_BASENAME}_xvfb.log"
    Xvfb :0 -auth ~/.Xauthority -screen 0 640x480x24 >> "${LOG_DIR}/${LOG_BASENAME}_xvfb.log" 2>&1 &
    sleep 1

    echo "Starting VNC server" ${LOG_DIR}/${LOG_BASENAME}_xvnc.log
    x11vnc -forever -nopw -display :0 >> "${LOG_DIR}/${LOG_BASENAME}_xvnc.log" 2>&1 &
    sleep 1
}

function start_bot() {
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
            win_java32 \
                -jar "${BOT_EXECUTABLE}" \
                -Djava.library.path="$APP_DIR/requirements" \
                >> "${LOG_DIR}/${LOG_BASENAME}_bot.log" 2>&1

        elif [ "$BOT_TYPE" == "exe" ]; then
            wine "${BOT_EXECUTABLE}" \
                >> "${LOG_DIR}/${LOG_BASENAME}_bot.log" 2>&1
        fi

        popd
    } &

    . hook_after_bot_start.sh

}

function start_game() {
    . hook_before_game_start.sh

    # Launch the game!
    LOG_GAME="${LOG_DIR}/${LOG_BASENAME}_game.log"
    echo "Starting game, savings logs to $LOG_GAME"
    echo "------------------------------------------" >> "$LOG_GAME"
    echo "Started game at" `date +%Y-%m-%dT%H:%M:%S%z` >> "$LOG_GAME"
    launch_game "$@" >> "$LOG_GAME" 2>&1  &

    . hook_after_game_start.sh
}

function prepare_character() {
    mv "$SC_DIR/characters/default.spc" "$SC_DIR/characters/${PLAYER_NAME}.spc"
    mv "$SC_DIR/characters/default.mpc" "$SC_DIR/characters/${PLAYER_NAME}.mpc"
}

function check_bot_requirements() {
    # Make sure the bot file exists
    if [ ! -d "$BOT_DIR/$BOT_NAME" ]; then
        echo "Bot not found in '$BOT_DIR/$BOT_NAME'"
        exit 1
    fi

    # Make sure the bot file exists
    if [ ! -f "$BOT_DIR/$BOT_NAME/AI/$BOT_FILE" ]; then
        echo "Bot not found in '$BOT_DIR/$BOT_NAME/AI/$BOT_FILE'"
        exit 1
    fi

    # Make sure the BWAPI file exists
    if [ ! -f "$BOT_DIR/$BOT_NAME/BWAPI.dll" ]; then
        echo "Bot not found in '$BOT_DIR/$BOT_NAME/BWAPI.dll'"
        exit 1
    fi

    # Make sure that bot type is recognized
    if [ "$BOT_TYPE" != "jar" ] && [ "$BOT_TYPE" != "exe" ] && [ "$BOT_TYPE" != "dll" ]; then
        echo "Bot type can be only one of 'jar', 'exe', 'dll' but the type supplied is '$BOT_TYPE'"
        exit 1
    fi
}
