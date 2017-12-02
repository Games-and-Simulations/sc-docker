#!/usr/bin/env bash
# Follow output from logs.
# this works only for 1v1 game

GAME_NAME=$1

FILES=(`find -L . -regextype posix-egrep -regex ".*${GAME_NAME}.*(bot|game).*" -type f | sort`)
if [ ${#FILES[@]} -eq 0 ]; then
  echo "No files found for game '$GAME_NAME'"
  exit 1
fi

echo "Starting to watching files:"
echo ${FILES[0]}
echo ${FILES[1]}
echo ${FILES[2]}
echo ${FILES[3]}
sleep 1

tmux \
  new-session  "tail -f ${FILES[0]} ; read" \; \
  split-window "tail -f ${FILES[1]} ; read" \; \
  split-window "tail -f ${FILES[2]} ; read" \; \
  split-window "tail -f ${FILES[3]} ; read" \; \
  select-layout even-vertical
