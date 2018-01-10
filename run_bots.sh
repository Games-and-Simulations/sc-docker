#!/usr/bin/env bash
set +x

function usage {
    echo "Usage: $0 [options] BOT_1:RACE_1 BOT_2:RACE_2 ... BOT_N:RACE_N"
    echo ""
    echo "  BOT_1 ... BOT_N      Names of java bots (without .jar extension)"
    echo "  RACE_1 ... RACE_N    Races of bots - Z or T or P"
    echo "  -l, --logdir         Path to log dir, defaults to $(pwd)/logs"
    echo "  -b, --botdir         Path to bot dir, defaults to $(pwd)/bots"
    echo "  -m, --map            Map name (path to map), such as "
    echo ""
    echo "  -g, --gui,--headful  Show the game in GUI in bots that are joining (not hosting)"
    echo "                       the game. You can use VNC to connect. (find container IP address "
    echo "                       and connect to its port 5900, password is 'starcraft') "
    echo ""
    echo "  --local              Use local image instead of dockerhub image."
    echo ""
    echo "  -h, --help           Show this help"
}


OPTS=`getopt -o hl:b:m:g --long help,logdir:,botdir:,map:,gui,headful,local -n 'parse-options' -- "$@"`
if [ $? != 0 ] ; then echo "Failed parsing options." >&2 ; exit 1 ; fi
eval set -- "$OPTS"


BOT_DIR=$(pwd)/bots
LOG_DIR=$(pwd)/logs
SCRIPT_DIR=$(pwd)/scripts

MAP="sscai\(2)Benzene.scx"
IMAGE="ggaic/starcraft:play"
HEADFUL=""

while true; do
  case "$1" in
    -h | --help ) usage; exit 0; shift ;;
    -l | --logdir ) LOG_DIR="$2"; shift; shift ;;
    -b | --botdir ) BOT_DIR="$2"; shift; shift ;;
    -m | --map ) MAP="$2"; shift; shift ;;
    -g | --gui | --headful ) HEADFUL="--headful"; shift ;;
    --local ) IMAGE="starcraft:play"; shift ;;
    -- ) shift; break ;;
    * ) usage; exit 1; break ;;
  esac
done

# Generate game name.
#
# Game name in SC can be max 23 chars long.
# Let's use some of the first UUID chars as identifier,
# and store some other useful information into game name
# as well (like date, map and bots playing).
BOTS="$@"
GAME_NAME_LONG=$(cat /proc/sys/kernel/random/uuid)
GAME_NAME=${GAME_NAME_LONG:0:23}

# We need to create a subnet if it doesn't exist yet
# so that we have static IPs that can be used for identification
HAS_LOCAL_NET=$(docker network ls | grep local_net)
[ -z "${HAS_LOCAL_NET}" ] && docker network create --subnet=172.18.0.0/16 local_net

function LAUNCH_BOT {
    BOT=$1
    GAME_NAME=$2
    POSTFIX=$3

    docker run \
        --rm \
        --privileged \
        --name "${GAME_NAME}_${POSTFIX}_bot_${BOT}" \
        --volume "$BOT_DIR:/home/starcraft/.wine/drive_c/bot" \
        --volume "$LOG_DIR:/home/starcraft/logs" \
        --volume "$SCRIPT_DIR:/home/starcraft/scripts" \
        --net local_net \
        ${IMAGE} \
        scripts/play_entrypoint.sh "$@" > /dev/null
}

IS_FIRST=1
for BOT_RACE in ${BOTS}
do
    IFS=':' read -r -a _BOT_RACE <<< "$BOT_RACE"
    BOT="${_BOT_RACE[0]}"
    RACE="${_BOT_RACE[1]}"

    # Make sure we have further disambiguation in case same bots play against each other :)
    RANDOM_POSTFIX=$(cat /proc/sys/kernel/random/uuid)
    POSTFIX="${RANDOM_POSTFIX:0:4}"

    if [ ${IS_FIRST} -eq 1 ]; then
        LAUNCH_BOT ${BOT} ${GAME_NAME} ${POSTFIX} --race ${RACE} --map "C:\\sc\\maps\\${MAP}" --lan --host &
        IS_FIRST=0
    else
        LAUNCH_BOT ${BOT} ${GAME_NAME} ${POSTFIX} --race ${RACE} --lan --join ${HEADFUL} &
    fi
done

# If everything was ok, print game name
echo "$GAME_NAME"
