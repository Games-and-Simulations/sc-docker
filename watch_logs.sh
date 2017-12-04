#!/usr/bin/env bash
# Follow output from logs.
# this works only for 1v1 game

GAME_NAME=$1

FILES=(`find -L . -regextype posix-egrep -regex ".*${GAME_NAME}.*(bot|game).*" -type f | sort`)
if [ ${#FILES[@]} -eq 0 ]; then
  echo "No files found for game '$GAME_NAME'"
  exit 1
fi

if [ ! ${#FILES[@]} -eq 4 ]; then
  echo "Too many files (${#FILES[@]}) found for game '$GAME_NAME'."
  echo "Maybe use better game name disambiguation?"
  echo ""
  echo "Found files:"
  echo "${FILES[@]}"
  exit 1
fi

echo "Starting to watch log files:"
echo ${FILES[0]}
echo ${FILES[1]}
echo ${FILES[2]}
echo ${FILES[3]}
sleep 1

tmux \
  new-session  "watch tail -10 ${FILES[0]} ; read" \; \
  split-window "watch tail -10 ${FILES[1]} ; read" \; \
  split-window "watch tail -10 ${FILES[2]} ; read" \; \
  split-window "watch tail -10 ${FILES[3]} ; read" \; \
  select-layout even-vertical
