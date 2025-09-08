#!/bin/bash

# This script patches play_common.sh to integrate auto-debugging

PLAY_COMMON="/app/play_common.sh"

# Add auto-debug startup to the start_gui function
if ! grep -q "auto_debug_startup.sh" "$PLAY_COMMON"; then
    echo "Patching play_common.sh to integrate auto-debugging..."
    
    # Create a backup
    cp "$PLAY_COMMON" "$PLAY_COMMON.bak"
    
    # Add auto-debug startup after the VNC server starts
    sed -i '/x11vnc -forever -nopw -display :0/a \
\
    # Start auto-debugging if enabled\
    if [ "$AUTO_DEBUG" = "true" ] && [ -f /app/scripts/auto_debug_startup.sh ]; then\
        echo "Starting auto-debugging..."\
        /app/scripts/auto_debug_startup.sh &\
    fi' "$PLAY_COMMON"
    
    echo "Auto-debugging integration added to play_common.sh"
else
    echo "Auto-debugging already integrated in play_common.sh"
fi
