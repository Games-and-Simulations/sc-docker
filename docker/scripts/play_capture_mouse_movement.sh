#!/usr/bin/env bash

while true
do
    # get X, Y in local scope
    eval $(xdotool getmouselocation --shell)
    if [ $X -lt "8" ]; then
        X="8"
    fi
    if [ $X -gt "632" ]; then
        X="632"
    fi
    if [ $Y -lt "8" ]; then
        Y="8"
    fi
    if [ $Y -gt "472" ]; then
        Y="472"
    fi

    if [ $X -eq "8" ] || [ $Y -eq "8" ] || [ $X -eq "632" ] || [ $Y -eq "472" ]; then
        xdotool mousemove $X $Y
        sleep 0.01
    fi
done

