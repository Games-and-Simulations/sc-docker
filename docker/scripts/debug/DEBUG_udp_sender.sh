#!/bin/bash
# Manual UDP Broadcast Sender for StarCraft LAN Discovery Testing
# Usage: ./udp_broadcast_sender.sh [port] [message] [target]

PORT=${1:-6111}
MESSAGE=${2:-"TEST_BROADCAST_$(date +%s)"}
TARGET=${3:-"255.255.255.255"}

echo "Sending UDP broadcast to $TARGET:$PORT"
echo "Message: $MESSAGE"

# Send UDP broadcast
echo "$MESSAGE" | socat - UDP4-DATAGRAM:$TARGET:$PORT,broadcast

echo "Broadcast sent successfully"

# Also show network info for debugging
MY_IP=$(hostname -I | cut -d" " -f1)
echo "My IP: $MY_IP"

# Show current network
ip route | grep default || true
ip addr show eth0 | grep inet || true
