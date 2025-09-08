#!/bin/bash
# Manual UDP Relay for StarCraft LAN Discovery
# Usage: ./udp_relay_manual.sh [port] [target_broadcast]

PORT=${1:-6111}
TARGET=${2:-"255.255.255.255"}

echo "Starting manual UDP relay on port $PORT"
echo "Forwarding to: $TARGET:$PORT"
echo "Press Ctrl+C to stop"

# Kill any existing relays on this port
pkill -f "UDP4-RECVFROM:${PORT}" 2>/dev/null

# Get container IP
MY_IP=$(hostname -I | cut -d" " -f1)
echo "Container IP: $MY_IP"

# Start relay
echo "Starting UDP relay..."
socat -u UDP4-RECVFROM:$PORT,broadcast,reuseaddr,fork UDP4-DATAGRAM:$TARGET:$PORT,broadcast &
RELAY_PID=$!

echo "Relay started with PID: $RELAY_PID"
echo "Monitoring relay process..."

# Wait for interrupt
trap "echo 'Stopping relay...'; kill $RELAY_PID 2>/dev/null; exit 0" INT

# Show relay status
while kill -0 $RELAY_PID 2>/dev/null; do
    sleep 5
    echo "$(date): Relay still running (PID: $RELAY_PID)"
done

echo "Relay stopped"
