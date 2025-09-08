#!/bin/bash

# Auto-start debugging script
# This script starts network debugging automatically after a delay

DELAY_SECONDS="${AUTO_DEBUG_DELAY:-10}"  # Default 10 seconds, configurable via env var
DEBUG_TIMEOUT="${AUTO_DEBUG_TIMEOUT:-120}"  # Default 2 minutes debugging

# Only start auto-debugging if AUTO_DEBUG env var is set
if [ "${AUTO_DEBUG:-}" != "true" ]; then
    echo "Auto-debugging disabled (AUTO_DEBUG not set to 'true')"
    exit 0
fi

echo "Auto-debug startup: waiting $DELAY_SECONDS seconds before starting network debugging..."
sleep "$DELAY_SECONDS"

# Start UDP relay to assist LAN discovery
if [ -x /app/scripts/udp_lan_relay.sh ]; then
    echo "Starting UDP LAN relay..."
    /app/scripts/udp_lan_relay.sh &
fi

echo "Starting automatic network debugging..."
/app/scripts/internal_network_debug.sh "$DEBUG_TIMEOUT" &

# Also log the auto-debug startup
echo "Auto-debug started at $(date) with PID $!" >> /debug_logs/auto_debug.log
