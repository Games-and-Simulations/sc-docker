#!/bin/bash
# Manual UDP Broadcast Receiver for StarCraft LAN Discovery
# Usage: ./udp_broadcast_receiver.sh [port] [logfile]

PORT=${1:-6111}
LOGFILE=${2:-"/tmp/udp_broadcast_${PORT}.log"}

echo "Starting UDP broadcast receiver on port $PORT"
echo "Logging to: $LOGFILE"
echo "Press Ctrl+C to stop"

# Kill any existing receivers on this port
pkill -f "UDP4-RECVFROM:${PORT}" 2>/dev/null

# Create log file
touch "$LOGFILE"

# Start broadcast receiver
echo "$(date): Starting UDP broadcast receiver on port $PORT" >> "$LOGFILE"
ncat -u -l "$PORT" >> "$LOGFILE" &
RECEIVER_PID=$!

echo "Receiver started with PID: $RECEIVER_PID"
echo "Monitor with: tail -f $LOGFILE"

# Wait for interrupt
trap "echo 'Stopping receiver...'; kill $RECEIVER_PID 2>/dev/null; exit 0" INT
wait $RECEIVER_PID
