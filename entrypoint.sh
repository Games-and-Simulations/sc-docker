#!/bin/bash

Xvfb :0 -auth ~/.Xauthority -screen 0 1024x768x24 >> ~/xvfb.log 2>&1 &
x11vnc -forever -passwd starcraft -display :0 >> ~/xvnc.log 2>&1 &

exec "$@"
