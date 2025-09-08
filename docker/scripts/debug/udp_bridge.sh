#!/bin/bash

# UDP Bridge for StarCraft LAN Discovery and Communication
# This script creates bidirectional UDP forwarding between containers

HOST_IP="172.20.0.13"
JOIN_IP="172.20.0.14"
BRIDGE_IP="172.20.0.1"  # Bridge gateway

echo "Starting UDP Bridge for StarCraft LAN"
echo "======================================"
echo "Host: $HOST_IP"
echo "Join: $JOIN_IP"
echo ""

# Kill any existing socat processes
pkill -f "socat.*6111" 2>/dev/null
pkill -f "socat.*6112" 2>/dev/null

# Function to create bidirectional UDP relay
create_relay() {
    local PORT=$1
    local DESC=$2
    
    echo "Setting up relay for port $PORT ($DESC)..."
    
    # Create a UDP proxy that forwards between containers
    # Listen on bridge interface and forward to both containers
    socat -T1 UDP4-RECVFROM:$PORT,broadcast,reuseaddr,fork \
          EXEC:"bash -c 'cat >&3' | tee >(socat - UDP4-SENDTO:$HOST_IP:$PORT) >(socat - UDP4-SENDTO:$JOIN_IP:$PORT)" &
    
    # Alternative: Simple broadcast repeater
    socat -T1 UDP4-RECVFROM:$PORT,reuseaddr,fork \
          UDP4-DATAGRAM:172.20.255.255:$PORT,broadcast,range=172.20.0.0/16 &
}

# Start relays for both StarCraft ports
create_relay 6111 "Discovery"
create_relay 6112 "Game Data"

# Also create direct forwarding rules using iptables
echo "Adding iptables forwarding rules..."
sudo iptables -t nat -A PREROUTING -p udp --dport 6111 -j DNAT --to-destination 172.20.255.255:6111
sudo iptables -t nat -A PREROUTING -p udp --dport 6112 -j DNAT --to-destination 172.20.255.255:6112

echo ""
echo "UDP Bridge is running!"
echo "Press Ctrl+C to stop"

# Keep script running
trap "pkill -f 'socat.*611'; exit" INT TERM
while true; do
    sleep 1
done
