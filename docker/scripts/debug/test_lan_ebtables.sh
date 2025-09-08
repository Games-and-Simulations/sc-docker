#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${GREEN}StarCraft LAN Discovery with ebtables - Rootful Podman${NC}"
echo "========================================================="

# Check for ebtables
if ! command -v ebtables &> /dev/null; then
    echo -e "${YELLOW}Installing ebtables for L2 broadcast support...${NC}"
    sudo pacman -S --noconfirm ebtables || sudo apt-get install -y ebtables || sudo dnf install -y ebtables
fi

# Configuration
NETWORK="sc_net"
IMAGE="starcraft:game"
MAPS_DIR="$HOME/.scbw/maps"
BOTS_DIR="$HOME/.scbw/bots:ro"
LOGS_DIR="$HOME/.scbw/logs"
GAMES_DIR="$HOME/.scbw/games"

# Ensure directories exist with proper permissions
mkdir -p "$LOGS_DIR" "$GAMES_DIR"
chmod 777 "$LOGS_DIR" "$GAMES_DIR"

# Clean up existing containers
echo -e "${YELLOW}Cleaning up existing containers...${NC}"
sudo podman stop sc-lan-host sc-lan-join 2>/dev/null
sudo podman rm sc-lan-host sc-lan-join 2>/dev/null

# Clean up function
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    sudo podman stop sc-lan-host sc-lan-join 2>/dev/null
    sudo podman rm sc-lan-host sc-lan-join 2>/dev/null
    # Remove ebtables rules
    sudo ebtables -D FORWARD -p IPv4 --ip-dst 255.255.255.255 -j ACCEPT 2>/dev/null
    sudo ebtables -D FORWARD -p IPv4 --ip-proto udp --ip-dport 6111:6112 -j ACCEPT 2>/dev/null
}

trap cleanup EXIT

# Start HOST container with all required environment variables
echo -e "\n${YELLOW}1. Starting HOST container...${NC}"
sudo podman run -d \
    --name sc-lan-host \
    --network $NETWORK \
    --cap-add ALL \
    --security-opt label=disable \
    -p 5900:5900 \
    -v "$MAPS_DIR:/app/sc/maps:ro" \
    -v "$LOGS_DIR:/app/logs:rw" \
    -v "$GAMES_DIR:/app/games:rw" \
    -e PLAYER_NAME="HostPlayer" \
    -e PLAYER_RACE="T" \
    -e GAME_NAME="TestGame" \
    -e GAME_TYPE="Free For All" \
    -e MAP_NAME="/(2)Benzene.scx" \
    -e GAME_SPEED=0 \
    -e HIDE_NAMES=0 \
    -e SPEED_OVERRIDE=0 \
    -e DROP_PLAYERS=0 \
    -e AUTO_DEBUG=false \
    -e HEADFUL=1 \
    -e HEADFUL_AUTO_LAUNCH=0 \
    -e JAVA_DEBUG=0 \
    -e IS_REPLAY=0 \
    -e NUM_PLAYERS=2 \
    -e BWAPI_DATA_BWTA_DIR="/app/sc/bwapi-data/BWTA" \
    -e BWAPI_DATA_BWTA2_DIR="/app/sc/bwapi-data/BWTA2" \
    -e BWAPI_DATA_DIR="/app/sc/bwapi-data" \
    -e BOT_DIR="/app/sc/bots" \
    -e BOT_EXECUTABLE="/app/sc/bots/HostBot" \
    -e BOT_FILE="/app/sc/bots/HostBot" \
    -e CONFIG_DIR="/app/sc/bwapi-data" \
    -e LOG_DIR="/app/logs" \
    -e MAP_DIR="/app/sc/maps" \
    -e PLAY_DIR="/app" \
    -e REPLAY_DIR="/app/replays" \
    -e SC_DIR="/app/sc" \
    -e TM_DIR="/app/sc/tm" \
    $IMAGE \
    /app/play_human.sh

# Start JOIN container
echo -e "\n${YELLOW}2. Starting JOIN container...${NC}"
sudo podman run -d \
    --name sc-lan-join \
    --network $NETWORK \
    --cap-add ALL \
    --security-opt label=disable \
    -p 5901:5900 \
    -v "$MAPS_DIR:/app/sc/maps:ro" \
    -v "$LOGS_DIR:/app/logs:rw" \
    -v "$GAMES_DIR:/app/games:rw" \
    -e PLAYER_NAME="JoinPlayer" \
    -e PLAYER_RACE="P" \
    -e GAME_NAME="TestGame" \
    -e GAME_TYPE="Free For All" \
    -e MAP_NAME="/(2)Benzene.scx" \
    -e GAME_SPEED=0 \
    -e HIDE_NAMES=0 \
    -e SPEED_OVERRIDE=0 \
    -e DROP_PLAYERS=0 \
    -e AUTO_DEBUG=false \
    -e HEADFUL=1 \
    -e HEADFUL_AUTO_LAUNCH=0 \
    -e JAVA_DEBUG=0 \
    -e IS_REPLAY=0 \
    -e NUM_PLAYERS=2 \
    -e BWAPI_DATA_BWTA_DIR="/app/sc/bwapi-data/BWTA" \
    -e BWAPI_DATA_BWTA2_DIR="/app/sc/bwapi-data/BWTA2" \
    -e BWAPI_DATA_DIR="/app/sc/bwapi-data" \
    -e BOT_DIR="/app/sc/bots" \
    -e BOT_EXECUTABLE="/app/sc/bots/JoinBot" \
    -e BOT_FILE="/app/sc/bots/JoinBot" \
    -e CONFIG_DIR="/app/sc/bwapi-data" \
    -e LOG_DIR="/app/logs" \
    -e MAP_DIR="/app/sc/maps" \
    -e PLAY_DIR="/app" \
    -e REPLAY_DIR="/app/replays" \
    -e SC_DIR="/app/sc" \
    -e TM_DIR="/app/sc/tm" \
    $IMAGE \
    /app/play_human.sh

# Wait for containers to start
sleep 5

# Get container IPs
HOST_IP=$(sudo podman inspect sc-lan-host | jq -r '.[0].NetworkSettings.Networks.sc_net.IPAddress')
JOIN_IP=$(sudo podman inspect sc-lan-join | jq -r '.[0].NetworkSettings.Networks.sc_net.IPAddress')
echo -e "${GREEN}Host IP: $HOST_IP${NC}"
echo -e "${GREEN}Join IP: $JOIN_IP${NC}"

# Configure the bridge with comprehensive broadcast support
echo -e "\n${YELLOW}3. Configuring network for full broadcast support...${NC}"
BRIDGE_NAME=$(sudo podman network inspect $NETWORK | jq -r '.[0].network_interface')
if [ -n "$BRIDGE_NAME" ] && [ "$BRIDGE_NAME" != "null" ]; then
    echo "Bridge interface: $BRIDGE_NAME"
    
    # Enable broadcast at kernel level
    sudo sysctl -w net.ipv4.conf.$BRIDGE_NAME.bc_forwarding=1
    sudo sysctl -w net.ipv4.conf.all.bc_forwarding=1
    sudo sysctl -w net.ipv4.icmp_echo_ignore_broadcasts=0
    sudo sysctl -w net.bridge.bridge-nf-call-iptables=0
    sudo sysctl -w net.bridge.bridge-nf-call-ip6tables=0
    sudo sysctl -w net.bridge.bridge-nf-call-arptables=0
    
    # Configure bridge interface
    sudo ip link set $BRIDGE_NAME multicast on
    sudo ip link set $BRIDGE_NAME promisc on
    sudo bridge link set dev $BRIDGE_NAME flood on 2>/dev/null
    
    # Add ebtables rules for L2 broadcast forwarding
    echo "Adding ebtables rules for broadcast..."
    sudo ebtables -A FORWARD -p IPv4 --ip-dst 255.255.255.255 -j ACCEPT
    sudo ebtables -A FORWARD -p IPv4 --ip-proto udp --ip-dport 6111:6112 -j ACCEPT
    
    # Add iptables rules
    sudo iptables -I FORWARD -i $BRIDGE_NAME -o $BRIDGE_NAME -j ACCEPT
    sudo iptables -I FORWARD -i $BRIDGE_NAME -o $BRIDGE_NAME -d 255.255.255.255/32 -j ACCEPT
    sudo iptables -I FORWARD -i $BRIDGE_NAME -o $BRIDGE_NAME -d 172.20.255.255/32 -j ACCEPT
    sudo iptables -t nat -I POSTROUTING -s 172.20.0.0/16 -d 255.255.255.255/32 -j RETURN
    
    echo -e "${GREEN}✓${NC} Network configured for broadcast"
fi

# Configure containers for broadcast
echo -e "\n${YELLOW}4. Configuring containers for broadcast...${NC}"
sudo podman exec sc-lan-host bash -c "
    ip link set eth0 multicast on
    ip link set eth0 promisc on
    echo 1 > /proc/sys/net/ipv4/ip_forward
    echo 0 > /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts
"
sudo podman exec sc-lan-join bash -c "
    ip link set eth0 multicast on
    ip link set eth0 promisc on
    echo 1 > /proc/sys/net/ipv4/ip_forward
    echo 0 > /proc/sys/net/ipv4/icmp_echo_ignore_broadcasts
"

# Test connectivity
echo -e "\n${YELLOW}5. Testing network connectivity...${NC}"

# Test basic connectivity
sudo podman exec sc-lan-host ping -c 1 -W 1 $JOIN_IP > /dev/null 2>&1 && \
    echo -e "${GREEN}✓ Host can ping Join${NC}" || \
    echo -e "${YELLOW}⚠ Host cannot ping Join (may be blocked by firewall)${NC}"

# Test broadcast with multiple methods
echo -e "\n${YELLOW}6. Testing UDP broadcast methods...${NC}"

# Method 1: Direct broadcast test
echo "Testing direct UDP broadcast..."
sudo podman exec -d sc-lan-host bash -c "timeout 5 nc -luk 0.0.0.0 6111 > /app/logs/broadcast-test.txt"
sleep 1
sudo podman exec sc-lan-join bash -c "echo 'DIRECT_BROADCAST' | nc -u -b -w1 255.255.255.255 6111" 2>/dev/null
sleep 1
if sudo podman exec sc-lan-host cat /app/logs/broadcast-test.txt 2>/dev/null | grep -q "DIRECT_BROADCAST"; then
    echo -e "${GREEN}✓ Direct broadcast working${NC}"
else
    echo -e "${YELLOW}⚠ Direct broadcast not working, trying subnet...${NC}"
    
    # Method 2: Subnet broadcast
    sudo podman exec -d sc-lan-host bash -c "timeout 5 nc -luk 0.0.0.0 6111 > /app/logs/subnet-test.txt"
    sleep 1
    sudo podman exec sc-lan-join bash -c "echo 'SUBNET_BROADCAST' | nc -u -w1 172.20.255.255 6111" 2>/dev/null
    sleep 1
    if sudo podman exec sc-lan-host cat /app/logs/subnet-test.txt 2>/dev/null | grep -q "SUBNET_BROADCAST"; then
        echo -e "${GREEN}✓ Subnet broadcast working${NC}"
    fi
fi

# Check StarCraft status
echo -e "\n${YELLOW}7. Checking StarCraft status...${NC}"
sudo podman exec sc-lan-host pgrep -x "StarCraft.exe" > /dev/null && \
    echo -e "${GREEN}✓ StarCraft running on HOST${NC}" || \
    echo -e "${RED}✗ StarCraft not running on HOST${NC}"
    
sudo podman exec sc-lan-join pgrep -x "StarCraft.exe" > /dev/null && \
    echo -e "${GREEN}✓ StarCraft running on JOIN${NC}" || \
    echo -e "${RED}✗ StarCraft not running on JOIN${NC}"

# Start packet capture
echo -e "\n${YELLOW}8. Starting packet capture...${NC}"
sudo podman exec -d sc-lan-host tcpdump -i eth0 -w /app/logs/host-lan.pcap 'udp port 6111 or udp port 6112'
sudo podman exec -d sc-lan-join tcpdump -i eth0 -w /app/logs/join-lan.pcap 'udp port 6111 or udp port 6112'

echo -e "\n${MAGENTA}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}VNC Access:${NC}"
echo "  • Host: vncviewer localhost:5900"
echo "  • Join: vncviewer localhost:5901"
echo ""
echo -e "${BLUE}To test LAN discovery:${NC}"
echo "  1. Connect to HOST via VNC (port 5900)"
echo "  2. Navigate to: Multiplayer → Local Area Network (UDP)"
echo "  3. Click 'Create Game' and set up the game"
echo "  4. Connect to JOIN via VNC (port 5901)"
echo "  5. Navigate to: Multiplayer → Local Area Network (UDP)"
echo "  6. The host's game should appear in the list"
echo "  7. Click on the game to join"
echo ""
echo -e "${BLUE}Debug commands:${NC}"
echo "  • View HOST logs: sudo podman logs sc-lan-host"
echo "  • View JOIN logs: sudo podman logs sc-lan-join"
echo "  • Check network: sudo podman exec sc-lan-host netstat -uln"
echo "  • Test broadcast: sudo podman exec sc-lan-join bash -c 'echo test | nc -u -b 255.255.255.255 6111'"
echo ""
echo -e "${YELLOW}Monitoring network traffic...${NC}"
echo "(Press Ctrl+C to stop)"
echo ""

# Monitor traffic
while true; do
    # Show any UDP traffic on StarCraft ports
    sudo timeout 5 podman exec sc-lan-host tcpdump -i eth0 -nn -c 5 'udp port 6111 or udp port 6112' 2>/dev/null | while read line; do
        [[ ! -z "$line" ]] && echo -e "${GREEN}[HOST]${NC} $line"
    done
    
    sudo timeout 5 podman exec sc-lan-join tcpdump -i eth0 -nn -c 5 'udp port 6111 or udp port 6112' 2>/dev/null | while read line; do
        [[ ! -z "$line" ]] && echo -e "${YELLOW}[JOIN]${NC} $line"
    done
    
    sleep 2
done
