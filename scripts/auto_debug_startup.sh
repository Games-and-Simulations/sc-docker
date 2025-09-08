#!/bin/bash

# Auto-debugging startup script
# This script automatically starts network debugging when AUTO_DEBUG=true

set -e

# Check if auto-debugging is enabled
if [ "$AUTO_DEBUG" != "true" ]; then
    echo "Auto-debugging not enabled (AUTO_DEBUG=$AUTO_DEBUG)"
    exit 0
fi

# Default values
DELAY=${AUTO_DEBUG_DELAY:-10}
TIMEOUT=${AUTO_DEBUG_TIMEOUT:-120}
DEBUG_DIR=${DEBUG_DIR:-/debug_logs}

echo "Auto-debugging enabled:"
echo "  Delay: ${DELAY}s"
echo "  Timeout: ${TIMEOUT}s" 
echo "  Debug directory: ${DEBUG_DIR}"

# Wait for the specified delay
echo "Waiting ${DELAY} seconds before starting debugging..."
sleep "$DELAY"

# Check if debug directory is available
if [ ! -d "$DEBUG_DIR" ]; then
    echo "Warning: Debug directory $DEBUG_DIR not found, debugging disabled"
    exit 0
fi

# Start internal network debugging
if [ -f /app/scripts/internal_network_debug.sh ]; then
    echo "Starting internal network debugging..."
    /app/scripts/internal_network_debug.sh "$TIMEOUT" "$DEBUG_DIR" &
    DEBUG_PID=$!
    echo "Network debugging started with PID: $DEBUG_PID"
    
    # Optional: wait for debugging to complete
    # wait $DEBUG_PID
else
    echo "Warning: internal_network_debug.sh not found"
fi

echo "Auto-debugging startup complete"
