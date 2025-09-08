#!/usr/bin/env bash

echo "hook: before game start"

# Handle LastReplay.rep removal gracefully - this is done in the hook rather than 
# in the main script to avoid bash set -e causing the script to exit on permission errors
if [ -f "$MAP_DIR/replays/LastReplay.rep" ]; then
    echo "Attempting to remove existing LastReplay.rep file..."
    if rm "$MAP_DIR/replays/LastReplay.rep" 2>/dev/null; then
        echo "Successfully removed LastReplay.rep"
    else
        echo "Could not remove LastReplay.rep (likely permission issue), continuing anyway..."
        # Try to make it writable first, then remove it
        if chmod 664 "$MAP_DIR/replays/LastReplay.rep" 2>/dev/null && rm "$MAP_DIR/replays/LastReplay.rep" 2>/dev/null; then
            echo "Successfully removed LastReplay.rep after chmod"
        else
            echo "Still could not remove LastReplay.rep, will proceed with game startup"
        fi
    fi
fi
