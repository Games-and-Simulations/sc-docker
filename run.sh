#!/usr/bin/env bash

RUN_BOT="purple_bot"

docker run --rm -it \
           --net host \
           --privileged \
           starcraft:${RUN_BOT} \
           /bin/bash -c "
                set -x;
                ~/launch_game.sh;
                java -jar bot.jar;
                sleep 10" # sleep for now, because bot will exist immediately (32bit issue)
