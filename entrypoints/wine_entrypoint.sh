#!/bin/bash
set -eux


Xvfb :0 -auth ~/.Xauthority -screen 0 1024x768x24 >> ${LOG_DIR}/xvfb.log 2>&1 &
x11vnc -forever -passwd starcraft -display :0 >> ${LOG_DIR}/xvnc.log 2>&1 &

exec "$@"
