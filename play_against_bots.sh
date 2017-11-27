#!/usr/bin/env bash
set -eu

function usage {
    echo "Usage: $0 [options] BOT_1:RACE_1 BOT_2:RACE_2 ... BOT_N:RACE_N"
    echo ""
    echo "  BOT_1 ... BOT_N      Names of java bots (without .jar extension)"
    echo "  RACE_1 ... RACE_N    Races of bots - Z or T or P"
    echo "  -l, --logdir         Path to log dir, defaults to $(pwd)/logs"
    echo "  -b, --botdir         Path to bot dir, defaults to $(pwd)/bots"
    echo ""
    echo "  -h, --help           Show this help"
}

OPTS=`getopt -o hl:b: --long help,logdir:,botdir: -n 'parse-options' -- "$@"`
if [ $? != 0 ] ; then echo "Failed parsing options." >&2 ; exit 1 ; fi
eval set -- "$OPTS"

BOT_DIR=$(pwd)/bots
LOG_DIR=$(pwd)/logs

while true; do
  case "$1" in
    -h | --help ) usage; exit 0; shift ;;
    -l | --logdir ) LOG_DIR="$2"; shift; shift ;;
    -b | --botdir ) BOT_DIR="$2"; shift; shift ;;
    -- ) shift; break ;;
    * ) usage; exit 1; break ;;
  esac
done

docker run \
        --rm -d \
        --privileged \
        --volume "$LOG_DIR:/home/starcraft/logs" \
        --net host \
        starcraft:play \
        launch_game.sh --headful

echo "First setup the game:"
echo " - run multiplayer on Expension"
echo " - choose multi player on Local Area Network (UDP)"
echo " - create game"
echo " - choose a map"
echo ""
echo "Now bots will be able to connect!"

read -p "Press enter when you have done the above ^^ "

GAME_NAME="human_against_bots"

function LAUNCH_BOT {
    docker run \
        --rm -d \
        --privileged \
        --volume "$BOT_DIR:/home/starcraft/.wine/drive_c/bot" \
        --volume "$LOG_DIR:/home/starcraft/logs" \
        --net local_net \
        starcraft:play \
        play_entrypoint.sh "$@" > /dev/null
}

BOTS="$@"

# We need to create a subnet if it doesn't exist yet
# so that we have static IPs that can be used for identification
HAS_LOCAL_NET=$(docker network ls | grep local_net)
[ -z "${HAS_LOCAL_NET}" ] && docker network create --subnet=172.18.0.0/16 local_net

for BOT_RACE in ${BOTS}
do
    IFS=':' read -r -a _BOT_RACE <<< "$BOT_RACE"
    BOT="${_BOT_RACE[0]}"
    RACE="${_BOT_RACE[1]}"

    echo "Launching $BOT"
    LAUNCH_BOT ${BOT} "${GAME_NAME}" --race ${RACE} --lan --join
done

echo "Wait for bots to connect and play!"
