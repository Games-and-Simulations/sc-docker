#!/usr/bin/env bash
# Follow output from logs.
# this works only for 1v1 game

GAME_NAME=$1

FILES=(`find . -name "*${GAME_NAME}*" | sort`)
tmux \
  new-session  "tail -f ${FILES[1]} ; read" \; \
  split-window "tail -f ${FILES[2]} ; read" \; \
  split-window "tail -f ${FILES[3]} ; read" \; \
  split-window "tail -f ${FILES[4]} ; read" \; \
  select-layout even-vertical
