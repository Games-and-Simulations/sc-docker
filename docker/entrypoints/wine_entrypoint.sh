#!/bin/bash
set -eu

Xvfb :0 -auth ~/.Xauthority -screen 0 640x480x24 >> ${LOG_DIR}/xvfb.log 2>&1 &
x11vnc -forever -nopw -display :0 >> ${LOG_DIR}/xvnc.log 2>&1 &

exec "$@"
