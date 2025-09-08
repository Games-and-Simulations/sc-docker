#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  StarCraft LAN Discovery - Bridge Network Solution${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""

# Configuration
NETWORK="sc_net"
IMAGE="starcraft:game"
MAPS_DIR="$HOME/.scbw/maps"
LOGS_DIR="$HOME/.scbw/logs"
GAMES_DIR="$HOME/.scbw/games"

# Ensure directories exist with proper permissions
mkdir -p "$LOGS_DIR" "$GAMES_DIR"
chmod 777 "$LOGS_DIR" "$GAMES_DIR"

# Clean up existing containers
echo -e "${YELLOW}Cleaning up existing containers...${NC}"
sudo podman stop sc-bridge-host sc-bridge-join sc-relay 2>/dev/null
sudo podman rm sc-bridge-host sc-bridge-join sc-relay 2>/dev/null

# Clean up function
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    sudo podman stop sc-bridge-host sc-bridge-join sc-relay 2>/dev/null
    sudo podman rm sc-bridge-host sc-bridge-join sc-relay 2>/dev/null
    pkill -f udp_broadcast_relay.py 2>/dev/null
}

trap cleanup EXIT

# Ensure network exists
echo -e "${YELLOW}Ensuring bridge network exists...${NC}"
sudo podman network ls | grep -q $NETWORK || sudo podman network create --driver bridge --subnet 172.20.0.0/16 $NETWORK

# Start HOST container with proper display settings
echo -e "\n${YELLOW}1. Starting HOST container...${NC}"
sudo podman run -d \
    --name sc-bridge-host \
    --network $NETWORK \
    --cap-add NET_RAW \
    --cap-add NET_ADMIN \
    -p 5900:5900 \
    -v "$MAPS_DIR:/app/sc/maps:ro" \
    -v "$LOGS_DIR:/app/logs:rw" \
    -v "$GAMES_DIR:/app/games:rw" \
    -e DISPLAY=:99 \
    $IMAGE \
    bash -c "
        # Start Xvfb with 16-bit color and 640x480 (native SC resolution)
        Xvfb :99 -screen 0 640x480x16 -ac &
        sleep 2
        
        # Start VNC
        x11vnc -forever -nopw -display :99 -rfbport 5900 -scale 1:1 -viewonly off &
        
        # Install DirectPlay if needed
        if ! wine reg query 'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\DirectPlay' 2>/dev/null | grep -q DirectPlay; then
            echo 'Installing DirectPlay...'
            winetricks -q directplay 2>/dev/null || true
        fi
        
        # Configure Wine
        export WINEDEBUG=-all
        export WINEPREFIX=/app/wine
        
        # Start StarCraft
        echo 'Starting StarCraft HOST...'
        cd /app/sc
        wine StarCraft.exe &
        
        # Monitor
        while true; do
            if pgrep -x 'StarCraft.exe' > /dev/null; then
                echo 'HOST: StarCraft running'
            else
                echo 'HOST: StarCraft stopped'
            fi
            sleep 30
        done
    "

# Wait for host to start
sleep 5

# Get host IP
HOST_IP=$(sudo podman inspect sc-bridge-host | jq -r '.[0].NetworkSettings.Networks.sc_net.IPAddress')
echo -e "${GREEN}Host container IP: $HOST_IP${NC}"

# Start JOIN container
echo -e "\n${YELLOW}2. Starting JOIN container...${NC}"
sudo podman run -d \
    --name sc-bridge-join \
    --network $NETWORK \
    --cap-add NET_RAW \
    --cap-add NET_ADMIN \
    -p 5901:5900 \
    -v "$MAPS_DIR:/app/sc/maps:ro" \
    -v "$LOGS_DIR:/app/logs:rw" \
    -v "$GAMES_DIR:/app/games:rw" \
    -e DISPLAY=:99 \
    $IMAGE \
    bash -c "
        # Start Xvfb with 16-bit color and 640x480
        Xvfb :99 -screen 0 640x480x16 -ac &
        sleep 2
        
        # Start VNC
        x11vnc -forever -nopw -display :99 -rfbport 5900 -scale 1:1 -viewonly off &
        
        # Install DirectPlay if needed
        if ! wine reg query 'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\DirectPlay' 2>/dev/null | grep -q DirectPlay; then
            echo 'Installing DirectPlay...'
            winetricks -q directplay 2>/dev/null || true
        fi
        
        # Configure Wine
        export WINEDEBUG=-all
        export WINEPREFIX=/app/wine
        
        # Start StarCraft
        echo 'Starting StarCraft JOIN...'
        cd /app/sc
        wine StarCraft.exe &
        
        # Monitor
        while true; do
            if pgrep -x 'StarCraft.exe' > /dev/null; then
                echo 'JOIN: StarCraft running'
            else
                echo 'JOIN: StarCraft stopped'
            fi
            sleep 30
        done
    "

# Wait for join to start
sleep 5

# Get join IP
JOIN_IP=$(sudo podman inspect sc-bridge-join | jq -r '.[0].NetworkSettings.Networks.sc_net.IPAddress')
echo -e "${GREEN}Join container IP: $JOIN_IP${NC}"

# Configure bridge for broadcast
echo -e "\n${YELLOW}3. Configuring bridge network...${NC}"
BRIDGE_NAME=$(sudo podman network inspect $NETWORK | jq -r '.[0].network_interface')
if [ -n "$BRIDGE_NAME" ] && [ "$BRIDGE_NAME" != "null" ]; then
    echo "Bridge interface: $BRIDGE_NAME"
    sudo sysctl -w net.ipv4.conf.all.bc_forwarding=1 2>/dev/null || true
    sudo sysctl -w net.ipv4.icmp_echo_ignore_broadcasts=0 2>/dev/null || true
    sudo ip link set $BRIDGE_NAME multicast on 2>/dev/null || true
    sudo ip link set $BRIDGE_NAME promisc on 2>/dev/null || true
    
    # iptables rules for broadcast
    sudo iptables -I FORWARD -i $BRIDGE_NAME -o $BRIDGE_NAME -j ACCEPT 2>/dev/null || true
    sudo iptables -I FORWARD -i $BRIDGE_NAME -o $BRIDGE_NAME -d 255.255.255.255/32 -j ACCEPT 2>/dev/null || true
    sudo iptables -I FORWARD -i $BRIDGE_NAME -o $BRIDGE_NAME -d 172.20.255.255/32 -j ACCEPT 2>/dev/null || true
fi

# Start UDP broadcast relay container
echo -e "\n${YELLOW}4. Starting UDP broadcast relay...${NC}"
sudo podman run -d \
    --name sc-relay \
    --network $NETWORK \
    --cap-add NET_RAW \
    --cap-add NET_ADMIN \
    -v "$(pwd)/udp_broadcast_relay.py:/relay.py:ro" \
    python:3-slim \
    bash -c "
        # Update container IPs in relay script
        sed -i \"s/172.20.0.2/$HOST_IP/g\" /relay.py
        sed -i \"s/172.20.0.3/$JOIN_IP/g\" /relay.py
        python3 /relay.py
    "

# Alternative: Run relay on host if container doesn't work
echo -e "\n${YELLOW}5. Starting host-based relay as backup...${NC}"
chmod +x udp_broadcast_relay.py
sudo python3 udp_broadcast_relay.py &
RELAY_PID=$!
echo "Relay PID: $RELAY_PID"

# Check status
echo -e "\n${YELLOW}6. Checking container status...${NC}"
sleep 3
sudo podman exec sc-bridge-host pgrep -x "StarCraft.exe" > /dev/null && \
    echo -e "${GREEN}✓ StarCraft HOST is running${NC}" || \
    echo -e "${RED}✗ StarCraft HOST not running${NC}"
    
sudo podman exec sc-bridge-join pgrep -x "StarCraft.exe" > /dev/null && \
    echo -e "${GREEN}✓ StarCraft JOIN is running${NC}" || \
    echo -e "${RED}✗ StarCraft JOIN not running${NC}"

echo -e "\n${MAGENTA}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}         SETUP COMPLETE - Bridge Network${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}VNC Access (640x480 native resolution):${NC}"
echo "  • Host: vncviewer localhost:5900"
echo "  • Join: vncviewer localhost:5901"
echo ""
echo -e "${BLUE}Network Configuration:${NC}"
echo "  • Network: Bridge (sc_net)"
echo "  • Host IP: $HOST_IP"
echo "  • Join IP: $JOIN_IP"
echo "  • UDP Relay: Active (forwarding broadcasts)"
echo ""
echo -e "${BLUE}To test LAN discovery:${NC}"
echo "  1. Connect to HOST via VNC (port 5900)"
echo "  2. Go to: Multiplayer → Local Area Network (UDP)"
echo "  3. Create a game"
echo "  4. Connect to JOIN via VNC (port 5901)"  
echo "  5. Go to: Multiplayer → Local Area Network (UDP)"
echo "  6. The game should appear in the list"
echo ""
echo -e "${GREEN}The UDP broadcast relay is forwarding discovery packets between containers${NC}"
echo ""
echo "Press Ctrl+C to stop all containers"

# Monitor relay output
echo -e "\n${YELLOW}Monitoring broadcast relay...${NC}"
while true; do
    sleep 5
done
