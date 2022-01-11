#!/usr/bin/env bash


function LOG() {
    echo `date +%Y-%m-%dT%H:%M:%S` "$@"
}

# From https://stackoverflow.com/a/24413646
#
# Usage: run_with_timeout N cmd args...
#    or: run_with_timeout cmd args...
# In the second case, cmd cannot be a number and the timeout will be 10 seconds.
#
# Exit code 143 means it exited with timeout
function run_with_timeout () {
    local time=10
    if [[ $1 =~ ^[0-9]+$ ]]; then time=$1; shift; fi
    # Run in a subshell to avoid job control messages
    ( "$@" &
      child=$!
      # Avoid default notification in non-interactive shell for SIGTERM
      trap -- "" SIGTERM
      ( sleep $time
        kill $child 2> /dev/null ) &
      wait $child
    )
}

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
    PLAYER_DLL="$1"

    LOG "Preparing bwapi.ini"
    BWAPI_INI="$BWAPI_DATA_DIR/bwapi.ini"

    MAP=$(echo $MAP_NAME | sed "s:$MAP_DIR:maps:g")
    RACE=$(fully_qualified_race_name ${PLAYER_RACE})

    sed -i "s:^ai = NULL:ai = $PLAYER_DLL:g" "${BWAPI_INI}"
    sed -i "s:^race = :race = $RACE:g" "${BWAPI_INI}"
    sed -i "s:^game_type = :game_type = $GAME_TYPE:g" "${BWAPI_INI}"
    sed -i "s:^save_replay = :save_replay = maps/replays/$REPLAY_FILE:g" "${BWAPI_INI}"
    sed -i "s:^wait_for_min_players = :wait_for_min_players = $NUM_PLAYERS:g" "${BWAPI_INI}"
    sed -i "s:^speed_override = :speed_override = $SPEED_OVERRIDE:g" "${BWAPI_INI}"
    sed -i "s:^seed_override = :seed_override = $SEED_OVERRIDE:g" "${BWAPI_INI}"

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

    if [ $DROP_PLAYERS -eq "1" ]; then
        sed -i "s:^drop_players = ON:drop_players = OFF:g" "${BWAPI_INI}"
    fi

    . hook_update_bwapi_ini.sh

    cat "$BWAPI_INI"
}

function start_gui() {
    if [ -z "${LOG_GUI+set}" ]; then
        LOG_XVFB="/dev/null"
        LOG_XVNC="/dev/null"
    else
        LOG_XVFB="${LOG_DIR}/xvfb.log"
        LOG_XVNC="${LOG_DIR}/xvnc.log"
    fi


    # Launch the GUI!
    LOG "Starting X, savings logs to " "$LOG_XVFB"
    Xvfb :0 -auth ~/.Xauthority -screen 0 640x480x24 >> "$LOG_XVFB" 2>&1 &
    sleep 1

    LOG "Starting VNC server" "$LOG_XVNC"
    x11vnc -forever -nopw -display :0 >> "$LOG_XVNC" 2>&1 &
    sleep 1
}

# Bot might use an server/client infrastructure, so connect it after the game has started
function connect_bot() {
    {
        pushd $SC_DIR

        if [ "$BOT_TYPE" == "dll" ] && [ -f "$BWAPI_DATA_DIR/AI/run_connect.bat" ]; then
            LOG "Running run_connect.bat for Module bot *AFTER* game has started." >> "$LOG_BOT"
            WINEPATH="$JAVA_DIR/bin" wine cmd /c "$BWAPI_DATA_DIR/AI/run_connect.bat" >> "${LOG_BOT}" 2>&1
        fi

        popd
    } &
}

function start_bot() {
    . hook_before_bot_start.sh

    if [ "$BOT_TYPE" == "dll" ]; then
        LOG "Module bot started by BWAPI" >> "$LOG_BOT"
        return 0
    fi

    # Launch the bot!
    LOG "Starting bot ${BOT_FILE}" >> "$LOG_BOT"
    echo "------------------------------------------" >> "$LOG_BOT"
    {
        pushd $SC_DIR

        DEBUG_CMD=""
        if [ "$JAVA_DEBUG" -eq "1" ]; then
            DEBUG_CMD="-Xdebug -agentlib:jdwp=transport=dt_socket,address="${JAVA_DEBUG_PORT}",server=y,suspend=y"
        fi

        # todo: run under "bot"
        if [ "$BOT_TYPE" != "dll" ] && [ -f "$BWAPI_DATA_DIR/AI/run_proxy.bat" ]; then
            WINEPATH="$JAVA_DIR/bin" wine cmd /c "$BWAPI_DATA_DIR/AI/run_proxy.bat" >> "${LOG_BOT}" 2>&1

        elif [ "$BOT_TYPE" == "jar" ]; then
            win_java32 \
                $DEBUG_CMD \
                $JAVA_OPTS \
                -jar "${BOT_EXECUTABLE}" \
                >> "${LOG_BOT}" 2>&1

        elif [ "$BOT_TYPE" == "exe" ]; then
            wine "${BOT_EXECUTABLE}" \
                >> "${LOG_BOT}" 2>&1

        elif [ "$BOT_TYPE" == "jython" ]; then
            win_java32 \
                -cp "${BOT_EXECUTABLE}" org.python.util.jython "$BOT_DATA_AI_DIR/__run__.py" \
                >> "${LOG_BOT}" 2>&1
        fi

        LOG "Bot exited." >> "$LOG_BOT"

        popd
    } &

    . hook_after_bot_start.sh

}

function start_game() {
    . hook_before_game_start.sh

    [ -f "$MAP_DIR/replays/LastReplay.rep" ] && rm "$MAP_DIR/replays/LastReplay.rep"

    update_registry

    # Launch the game!
    LOG "Starting game" >> "$LOG_GAME"
    echo "------------------------------------------" >> "$LOG_GAME"

    launch_game "$@" >> "$LOG_GAME" 2>&1  &

    . hook_after_game_start.sh
}

function prepare_character() {
    if [ "$HIDE_NAMES" == "0" ]; then
        mv "$SC_DIR/characters/player.spc" "$SC_DIR/characters/${PLAYER_NAME}.spc"
        mv "$SC_DIR/characters/player.mpc" "$SC_DIR/characters/${PLAYER_NAME}.mpc"
    fi
}

function prepare_tm() {
    cp ${TM_DIR}/${BOT_BWAPI}.dll $SC_DIR/tm.dll
}

function check_bot_requirements() {
    # Make sure the bot file exists
    if [ ! -f "$BOT_DIR/AI/$BOT_FILE" ]; then
        LOG "Bot not found in '$BOT_DIR/AI/$BOT_FILE'"
        exit 1
    fi

    # Make sure the BWAPI file exists
    if [ ! -f "$BOT_DIR/BWAPI.dll" ]; then
        LOG "Bot not found in '$BOT_DIR/BWAPI.dll'"
        exit 1
    fi

    # Make sure that bot type is recognized
    if [ "$BOT_TYPE" != "jar" ] && [ "$BOT_TYPE" != "exe" ] && [ "$BOT_TYPE" != "dll" ] && [ "$BOT_TYPE" != "jython" ]; then
        LOG "Bot type can be only one of 'jar', 'exe', 'dll', 'jython' but the type supplied is '$BOT_TYPE'"
        exit 1
    fi
}

function detect_game_finished() {
    while true
    do
        LOG "Checking game status ..." >> "$LOG_GAME"

        if ! pgrep -x "StarCraft.exe" > /dev/null
        then
            LOG "Game exited!" >> "$LOG_GAME"
            sleep 3
            return 0
        fi

        # Sometimes replay files are saved with .rep, or with .REP
        # note that ^^ works only in bash :)
        if [ -f "$SC_DIR/maps/replays/$REPLAY_FILE" ] || [ -f "$SC_DIR/maps/replays/${REPLAY_FILE^^}" ] || [ -f "$MAP_DIR/replays/LastReplay.rep" ] ;
        then
            LOG "Replays found." >> "$LOG_GAME"
            sleep 3
            return 0
        fi

        sleep 3
    done;
}

function update_registry() {
    # disable splash screen
    REG_KEY="HKEY_LOCAL_MACHINE\SOFTWARE\Blizzard Entertainment\Starcraft"
#    wine REG ADD "${REG_KEY}" /v Gamma /t REG_DWORD /d 0000008c
    wine REG ADD "${REG_KEY}" /v ColorCycle /t REG_DWORD /d 00000001
    wine REG ADD "${REG_KEY}" /v UnitPortraits /t REG_DWORD /d 00000002
    wine REG ADD "${REG_KEY}" /v speed /t REG_DWORD /d 00000006
    wine REG ADD "${REG_KEY}" /v mscroll /t REG_DWORD /d 00000001
    wine REG ADD "${REG_KEY}" /v kscroll /t REG_DWORD /d 00000001
    wine REG ADD "${REG_KEY}" /v m_mscroll /t REG_DWORD /d 00000003
    wine REG ADD "${REG_KEY}" /v m_kscroll /t REG_DWORD /d 00000003
#    wine REG ADD "${REG_KEY}" /v music /t REG_DWORD /d 0000002d
#    wine REG ADD "${REG_KEY}" /v sfx /t REG_DWORD /d 0000001e
    wine REG ADD "${REG_KEY}" /v tipnum /t REG_DWORD /d 00000001
    wine REG ADD "${REG_KEY}" /v intro /t REG_DWORD /d 00000200
    wine REG ADD "${REG_KEY}" /v introX /t REG_DWORD /d 00000000
    wine REG ADD "${REG_KEY}" /v unitspeech /t REG_DWORD /d 00000001
    wine REG ADD "${REG_KEY}" /v unitnoise /t REG_DWORD /d 00000002
    wine REG ADD "${REG_KEY}" /v bldgnoise /t REG_DWORD /d 00000004
    wine REG ADD "${REG_KEY}" /v tip /t REG_DWORD /d 00000100
    wine REG ADD "${REG_KEY}" /v trigtext /t REG_DWORD /d 00000400
    wine REG ADD "${REG_KEY}" /v StarEdit /t REG_EXPAND_SZ /d "Z:\app\sc\StarEdit.exe"
    wine REG ADD "${REG_KEY}" /v "Recent Maps"  /t REG_EXPAND_SZ /d ""
    wine REG ADD "${REG_KEY}" /v Retail /t REG_EXPAND_SZ /d "y"
    wine REG ADD "${REG_KEY}" /v Brood  /t REG_EXPAND_SZ /d "y"
    wine REG ADD "${REG_KEY}" /v StarCD /t REG_EXPAND_SZ /d ""
    wine REG ADD "${REG_KEY}" /v InstallPath /t REG_EXPAND_SZ /d "Z:\app\sc\\"
    wine REG ADD "${REG_KEY}" /v Program /t REG_EXPAND_SZ /d "Z:\app\sc\StarCraft.exe"

    REG_KEY="HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\Blizzard Entertainment\Starcraft\DelOpt0"
    wine REG ADD "${REG_KEY}" /v File0 /t REG_EXPAND_SZ /d "spc"
    wine REG ADD "${REG_KEY}" /v File1 /t REG_EXPAND_SZ /d "mpc"
    wine REG ADD "${REG_KEY}" /v Path0 /t REG_EXPAND_SZ /d "Z:\app\sc\characters"
    wine REG ADD "${REG_KEY}" /v Path1 /t REG_EXPAND_SZ /d "Z:\app\sc\characters"
}

function auto_launch() {
    # This a hacky way to go around "Unable to distribute map" bug
    # that I couldn't debug. Basically send appropriate keys to Starcraft to start the game.

    # todo: game type
    # todo: more testing
    SLEEP_TIME=0.1

    # Go to the map root directory
    xdotool key G
    sleep $SLEEP_TIME
    xdotool key Up
    sleep $SLEEP_TIME
    xdotool key Return
    sleep $SLEEP_TIME

    cd "$MAP_DIR"
    MAP_RELATIVE="${MAP_NAME/$MAP_DIR\//}"
    ADD_UP="" # If not in the root directory (as in the first loop), [Up One Level] is added
    for path_part in ${MAP_RELATIVE//// }; do
        FILES=$(echo "$(ls -p | grep -v / | grep '.*\.sc.*'| sort --ignore-case)")

        # We need to change directory
        if [ -d "$path_part" ]; then
            # If there are no files in CWD, then menu will start at the first directory
            if [ -z "$FILES" ]; then
                DIRS=$(echo -e "$(ls -d */ | sed 's/.$//')$ADD_UP" | sort --ignore-case)
                POSITION=$(grep -n "$path_part" <(echo "$DIRS") | cut -d: -f1)
                for i in `seq 2 $POSITION`;
                do
                    xdotool key Down
                    sleep $SLEEP_TIME
                done
            else
            # If there are map files in the CWD, cursor will start at the first file
                DIRS=$(echo -e "$(ls -d */ | sed 's/.$//')$ADD_UP" | sort --ignore-case -r)
                POSITION=$(grep -n "$path_part" <(echo "$DIRS") | cut -d: -f1)
                for i in `seq 1 $POSITION`;
                do
                    xdotool key Up
                    sleep $SLEEP_TIME
                done
            fi

            echo "cd $path_part"
            cd "$path_part"
        else
        # We need to select file
            POSITION=$(grep -n "$path_part" <(echo "$FILES") | cut -d: -f1)
            for i in `seq 2 $POSITION`;
            do
                xdotool key Down
                sleep $SLEEP_TIME
            done
        fi

        xdotool key Return
        sleep $SLEEP_TIME

        ADD_UP="\nUp One Level"
    done

    # Wait for players
    sleep 3

    # Position of the start button
    # (we have to click, because key press goes to chat at this point)
    xdotool mousemove 521 395 click 1
    xdotool mousemove 521 395 click 1
    xdotool mousemove 521 395 click 1
}

