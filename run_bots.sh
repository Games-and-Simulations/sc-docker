#!/usr/bin/env bash

BOT_DIR=/home/starcraft/.wine/drive_c/bot
LOG_DIR=/home/starcraft/logs

BOT_1=$1
BOT_2=$2

docker run \
   --rm -it \
   --net host \
   --privileged \
   --volume "$(pwd)/bots:$BOT_DIR" \
   --volume "$(pwd)/logs:$LOG_DIR" \
   starcraft:java \
   java_entrypoint.sh ${BOT_1} ${BOT_2}
