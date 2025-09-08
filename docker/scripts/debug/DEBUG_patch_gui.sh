#!/bin/bash
set -eux

# Patch play_bot.sh to always start GUI in debug mode
sed -i 's/if \[ "$IS_HEADFUL" == "1" \]; then/if [ "$IS_HEADFUL" == "1" ] || [ "$AUTO_DEBUG" == "1" ]; then/g' /app/play_bot.sh

# Patch play_human.sh if it exists and has similar logic
if [ -f /app/play_human.sh ]; then
    sed -i 's/if \[ "$IS_HEADFUL" == "1" \]; then/if [ "$IS_HEADFUL" == "1" ] || [ "$AUTO_DEBUG" == "1" ]; then/g' /app/play_human.sh
fi

echo "Debug GUI patch applied successfully"
