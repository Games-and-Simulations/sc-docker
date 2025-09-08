#!/usr/bin/env bash

echo "hook: update bwapi ini"

# Allow overriding auto_menu setting via environment variable
if [ -n "$BWAPI_AUTO_MENU" ]; then
    LOG "Setting auto_menu to $BWAPI_AUTO_MENU"
    sed -i "s:^auto_menu = .*:auto_menu = $BWAPI_AUTO_MENU:g" "${BWAPI_INI}"
fi

# Allow overriding lan_mode setting via environment variable
if [ -n "$BWAPI_LAN_MODE" ]; then
    LOG "Setting lan_mode to $BWAPI_LAN_MODE"
    sed -i "s:^lan_mode = .*:lan_mode = $BWAPI_LAN_MODE:g" "${BWAPI_INI}"
fi
