#!/usr/bin/env bash

echo "hook: init - starting UDP relay for LAN discovery"

# Only start UDP relay if we're in LAN mode
if [ "$BWAPI_AUTO_MENU" = "LAN" ] && [ "$BWAPI_LAN_MODE" = "Local Area Network (UDP)" ]; then
    # Check if socat is available
    if command -v socat &> /dev/null; then
        echo "Starting UDP broadcast relay for StarCraft LAN discovery..."
        
        # Get container's IP address
        MY_IP=$(hostname -I | cut -d" " -f1)
        echo "Container IP: $MY_IP"
        
        # Function to start relay on a specific port
        start_relay() {
            local PORT=$1
            local DESC=$2
            echo "Starting UDP relay on port $PORT ($DESC)..."
            
            # Create a single UDP relay that forwards all packets to broadcast address
            # This handles both incoming broadcasts and unicast packets
            socat -u UDP4-RECVFROM:$PORT,broadcast,reuseaddr,fork UDP4-DATAGRAM:255.255.255.255:$PORT,broadcast &
        }
        
        # Start relays for StarCraft LAN ports
        start_relay 6111 "Discovery"
        start_relay 6112 "Game data"
        
        # Give relays time to start
        sleep 1
        echo "UDP relay started successfully"
        
        # Log the socat processes for debugging
        ps aux | grep socat | grep -v grep
    else
        echo "Warning: socat not found, UDP relay not started (LAN discovery may not work)"
    fi
fi

echo "hook: init complete"
