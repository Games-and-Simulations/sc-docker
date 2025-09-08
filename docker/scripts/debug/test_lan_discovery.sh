#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}StarCraft LAN Discovery Test - Rootful Podman Bridge Network${NC}"
echo "=================================================="

# Configuration
NETWORK="sc_net"
IMAGE="starcraft:game"
MAPS_DIR="$HOME/.scbw/maps"
BOTS_DIR="$HOME/.scbw/bots"
LOGS_DIR="$HOME/.scbw/logs"
GAMES_DIR="$HOME/.scbw/games"

# Ensure directories exist with proper permissions
mkdir -p "$LOGS_DIR" "$GAMES_DIR"
chmod 777 "$LOGS_DIR" "$GAMES_DIR"

# Function to wait for container to be ready
wait_for_container() {
    local container=$1
    local max_wait=30
    local count=0
    
    while [ $count -lt $max_wait ]; do
        if sudo podman exec $container pgrep -x "StarCraft.exe" > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} $container: StarCraft.exe is running"
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done
    echo -e "${RED}✗${NC} $container: Timeout waiting for StarCraft.exe"
    return 1
}

# Clean up function
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    sudo podman stop sc-lan-host sc-lan-join 2>/dev/null
    sudo podman rm sc-lan-host sc-lan-join 2>/dev/null
}

trap cleanup EXIT

# Launch HOST container
echo -e "\n${YELLOW}1. Starting HOST container...${NC}"
sudo podman run -d \
    --name sc-lan-host \
    --network $NETWORK \
    --cap-add NET_RAW \
    --cap-add NET_ADMIN \
    --cap-add NET_BIND_SERVICE \
    --cap-add SYS_ADMIN \
    -p 5900:5900 \
    -v "$MAPS_DIR:/app/sc/maps:ro" \
    -v "$BOTS_DIR:/app/sc/bots:ro" \
    -v "$LOGS_DIR:/app/logs:rw" \
    -v "$GAMES_DIR:/app/games:rw" \
    -e PLAYER_NAME="HostBot" \
    -e PLAYER_RACE="T" \
    -e GAME_NAME="TestLAN" \
    -e GAME_TYPE="Free For All" \
    -e MAP_NAME="/(2)Benzene.scx" \
    -e GAME_SPEED=0 \
    -e HIDE_NAMES=0 \
    -e SPEED_OVERRIDE=0 \
    -e DROP_PLAYERS=0 \
    -e TM_LOG_RESULTS=1 \
    -e AUTO_DEBUG=false \
    -e HEADFUL_AUTO_LAUNCH=0 \
    -e JAVA_DEBUG=0 \
    $IMAGE \
    bash -c "
        # Enable broadcast on container interface
        ip link set eth0 multicast on
        ip link set eth0 promisc on
        
        # Start VNC
        x11vnc -forever -nopw -display :99 -rfbport 5900 &
        
        # Start StarCraft in LAN host mode
        echo 'Starting StarCraft as LAN host...'
        cd /app && wine /app/sc/StarCraft.exe &
        
        # Keep container running
        while true; do sleep 10; done
    "

# Wait for host to be ready
if ! wait_for_container "sc-lan-host"; then
    echo -e "${RED}Failed to start host container${NC}"
    exit 1
fi

# Get host container IP
HOST_IP=$(sudo podman inspect sc-lan-host | jq -r '.[0].NetworkSettings.Networks.sc_net.IPAddress')
echo -e "${GREEN}Host container IP: $HOST_IP${NC}"

# Wait a bit for host to initialize
echo "Waiting for host to initialize game..."
sleep 5

# Launch JOIN container
echo -e "\n${YELLOW}2. Starting JOIN container...${NC}"
sudo podman run -d \
    --name sc-lan-join \
    --network $NETWORK \
    --cap-add NET_RAW \
    --cap-add NET_ADMIN \
    --cap-add NET_BIND_SERVICE \
    --cap-add SYS_ADMIN \
    -p 5901:5900 \
    -v "$MAPS_DIR:/app/sc/maps:ro" \
    -v "$BOTS_DIR:/app/sc/bots:ro" \
    -v "$LOGS_DIR:/app/logs:rw" \
    -v "$GAMES_DIR:/app/games:rw" \
    -e PLAYER_NAME="JoinBot" \
    -e PLAYER_RACE="P" \
    -e GAME_NAME="TestLAN" \
    -e GAME_TYPE="Free For All" \
    -e MAP_NAME="/(2)Benzene.scx" \
    -e GAME_SPEED=0 \
    -e HIDE_NAMES=0 \
    -e SPEED_OVERRIDE=0 \
    -e DROP_PLAYERS=0 \
    -e TM_LOG_RESULTS=1 \
    -e AUTO_DEBUG=false \
    -e HEADFUL_AUTO_LAUNCH=0 \
    -e JAVA_DEBUG=0 \
    $IMAGE \
    bash -c "
        # Enable broadcast on container interface
        ip link set eth0 multicast on
        ip link set eth0 promisc on
        
        # Start VNC
        x11vnc -forever -nopw -display :99 -rfbport 5900 &
        
        # Start tcpdump to capture network traffic
        tcpdump -i eth0 -w /app/logs/join-network.pcap 'udp port 6111 or udp port 6112' &
        
        # Start StarCraft in LAN join mode
        echo 'Starting StarCraft as LAN joiner...'
        cd /app && wine /app/sc/StarCraft.exe &
        
        # Keep container running
        while true; do sleep 10; done
    "

# Wait for join to be ready
if ! wait_for_container "sc-lan-join"; then
    echo -e "${RED}Failed to start join container${NC}"
    exit 1
fi

# Get join container IP
JOIN_IP=$(sudo podman inspect sc-lan-join | jq -r '.[0].NetworkSettings.Networks.sc_net.IPAddress')
echo -e "${GREEN}Join container IP: $JOIN_IP${NC}"

# Configure bridge for broadcast/multicast (now that it exists)
echo -e "\n${YELLOW}3. Configuring bridge for broadcast/multicast...${NC}"
BRIDGE_NAME=$(sudo podman network inspect $NETWORK | jq -r '.[0].network_interface')
if [ -n "$BRIDGE_NAME" ] && [ "$BRIDGE_NAME" != "null" ]; then
    echo "Bridge interface: $BRIDGE_NAME"
    sudo ip link set $BRIDGE_NAME multicast on
    sudo ip link set $BRIDGE_NAME promisc on
    sudo sysctl -w net.ipv4.conf.$BRIDGE_NAME.bc_forwarding=1
    echo -e "${GREEN}✓${NC} Bridge configured for broadcast/multicast"
fi

# Test network connectivity
echo -e "\n${YELLOW}4. Testing network connectivity...${NC}"
sudo podman exec sc-lan-host ping -c 2 -W 1 $JOIN_IP > /dev/null 2>&1 && \
    echo -e "${GREEN}✓${NC} Host can ping Join" || \
    echo -e "${RED}✗${NC} Host cannot ping Join"

sudo podman exec sc-lan-join ping -c 2 -W 1 $HOST_IP > /dev/null 2>&1 && \
    echo -e "${GREEN}✓${NC} Join can ping Host" || \
    echo -e "${RED}✗${NC} Join cannot ping Host"

# Test UDP broadcast
echo -e "\n${YELLOW}5. Testing UDP broadcast...${NC}"
echo "Sending test broadcast from join container..."
sudo podman exec sc-lan-join bash -c "echo 'TEST_BROADCAST' | nc -u -b -w1 255.255.255.255 6111" 2>/dev/null

# Monitor for a moment
echo -e "\n${YELLOW}6. Monitoring network traffic (20 seconds)...${NC}"
echo "You can now:"
echo "  - VNC to host: vncviewer localhost:5900"
echo "  - VNC to join: vncviewer localhost:5901"
echo "  - Navigate to Multiplayer -> Local Area Network (UDP) in both"
echo ""

# Start monitoring in background
(
    sudo podman exec sc-lan-host tcpdump -i eth0 -n 'udp port 6111 or udp port 6112' 2>/dev/null | while read line; do
        echo -e "${GREEN}[HOST]${NC} $line"
    done
) &
HOST_TCPDUMP=$!

(
    sudo podman exec sc-lan-join tcpdump -i eth0 -n 'udp port 6111 or udp port 6112' 2>/dev/null | while read line; do
        echo -e "${YELLOW}[JOIN]${NC} $line"
    done
) &
JOIN_TCPDUMP=$!

# Wait and collect logs
sleep 20

# Kill tcpdump monitors
kill $HOST_TCPDUMP $JOIN_TCPDUMP 2>/dev/null

echo -e "\n${GREEN}Test setup complete!${NC}"
echo "Containers are running. Press Ctrl+C to stop and clean up."
echo ""
echo "To manually test:"
echo "1. VNC to host (port 5900) and create a LAN game"
echo "2. VNC to join (port 5901) and look for the game in LAN list"
echo ""
echo "Container logs:"
echo "  sudo podman logs sc-lan-host"
echo "  sudo podman logs sc-lan-join"

# Keep script running until interrupted
while true; do
    sleep 10
done
