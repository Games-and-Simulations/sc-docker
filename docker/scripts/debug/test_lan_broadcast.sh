#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}StarCraft LAN Broadcast Test - Rootful Podman${NC}"
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

# Clean up existing containers
echo -e "${YELLOW}Cleaning up existing containers...${NC}"
sudo podman stop sc-lan-host sc-lan-join 2>/dev/null
sudo podman rm sc-lan-host sc-lan-join 2>/dev/null

# Clean up function
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    sudo podman stop sc-lan-host sc-lan-join 2>/dev/null
    sudo podman rm sc-lan-host sc-lan-join 2>/dev/null
}

trap cleanup EXIT

# Launch HOST container with simplified command
echo -e "\n${YELLOW}1. Starting HOST container...${NC}"
sudo podman run -d \
    --name sc-lan-host \
    --network $NETWORK \
    --cap-add NET_RAW \
    --cap-add NET_ADMIN \
    --cap-add NET_BROADCAST \
    --sysctl net.ipv4.conf.all.bc_forwarding=1 \
    --sysctl net.ipv4.icmp_echo_ignore_broadcasts=0 \
    -p 5900:5900 \
    -v "$MAPS_DIR:/app/sc/maps:ro" \
    -v "$BOTS_DIR:/app/sc/bots:ro" \
    -v "$LOGS_DIR:/app/logs:rw" \
    -v "$GAMES_DIR:/app/games:rw" \
    -e DISPLAY=:99 \
    $IMAGE \
    bash -c "
        # Start Xvfb
        Xvfb :99 -screen 0 640x480x8 -ac &
        sleep 2
        
        # Start VNC
        x11vnc -forever -nopw -display :99 -rfbport 5900 &
        
        # Install DirectPlay components if missing
        if ! wine reg query 'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\DirectPlay' 2>/dev/null | grep -q DirectPlay; then
            echo 'Installing DirectPlay components...'
            winetricks -q directplay || true
        fi
        
        # Configure network interface for broadcast
        ip link set eth0 multicast on
        ip link set eth0 promisc on
        echo 1 > /proc/sys/net/ipv4/ip_forward
        
        # Start network monitoring
        echo 'Starting network monitor on HOST...'
        tcpdump -i eth0 -n 'udp port 6111 or udp port 6112' -w /app/logs/host-capture.pcap &
        
        # Start StarCraft
        echo 'Starting StarCraft as HOST...'
        cd /app/sc
        wine StarCraft.exe -join 255.255.255.255 &
        
        # Monitor and log
        while true; do
            if pgrep -x 'StarCraft.exe' > /dev/null; then
                echo 'StarCraft.exe is running on HOST'
            else
                echo 'StarCraft.exe stopped on HOST'
            fi
            sleep 10
        done
    "

# Wait for container to start
sleep 5

# Get host container IP
HOST_IP=$(sudo podman inspect sc-lan-host | jq -r '.[0].NetworkSettings.Networks.sc_net.IPAddress')
echo -e "${GREEN}Host container IP: $HOST_IP${NC}"

# Launch JOIN container
echo -e "\n${YELLOW}2. Starting JOIN container...${NC}"
sudo podman run -d \
    --name sc-lan-join \
    --network $NETWORK \
    --cap-add NET_RAW \
    --cap-add NET_ADMIN \
    --cap-add NET_BROADCAST \
    --sysctl net.ipv4.conf.all.bc_forwarding=1 \
    --sysctl net.ipv4.icmp_echo_ignore_broadcasts=0 \
    -p 5901:5900 \
    -v "$MAPS_DIR:/app/sc/maps:ro" \
    -v "$BOTS_DIR:/app/sc/bots:ro" \
    -v "$LOGS_DIR:/app/logs:rw" \
    -v "$GAMES_DIR:/app/games:rw" \
    -e DISPLAY=:99 \
    $IMAGE \
    bash -c "
        # Start Xvfb
        Xvfb :99 -screen 0 640x480x8 -ac &
        sleep 2
        
        # Start VNC
        x11vnc -forever -nopw -display :99 -rfbport 5900 &
        
        # Install DirectPlay components if missing
        if ! wine reg query 'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\DirectPlay' 2>/dev/null | grep -q DirectPlay; then
            echo 'Installing DirectPlay components...'
            winetricks -q directplay || true
        fi
        
        # Configure network interface for broadcast
        ip link set eth0 multicast on
        ip link set eth0 promisc on
        echo 1 > /proc/sys/net/ipv4/ip_forward
        
        # Start network monitoring
        echo 'Starting network monitor on JOIN...'
        tcpdump -i eth0 -n 'udp port 6111 or udp port 6112' -w /app/logs/join-capture.pcap &
        
        # Start StarCraft
        echo 'Starting StarCraft as JOIN...'
        cd /app/sc
        wine StarCraft.exe -join 255.255.255.255 &
        
        # Monitor and log
        while true; do
            if pgrep -x 'StarCraft.exe' > /dev/null; then
                echo 'StarCraft.exe is running on JOIN'
            else
                echo 'StarCraft.exe stopped on JOIN'
            fi
            sleep 10
        done
    "

# Wait for container to start
sleep 5

# Get join container IP
JOIN_IP=$(sudo podman inspect sc-lan-join | jq -r '.[0].NetworkSettings.Networks.sc_net.IPAddress')
echo -e "${GREEN}Join container IP: $JOIN_IP${NC}"

# Configure the Podman bridge
echo -e "\n${YELLOW}3. Configuring Podman bridge for broadcast...${NC}"
BRIDGE_NAME=$(sudo podman network inspect $NETWORK | jq -r '.[0].network_interface')
if [ -n "$BRIDGE_NAME" ] && [ "$BRIDGE_NAME" != "null" ]; then
    echo "Bridge interface: $BRIDGE_NAME"
    
    # Enable broadcast forwarding
    sudo sysctl -w net.ipv4.conf.$BRIDGE_NAME.bc_forwarding=1
    sudo sysctl -w net.ipv4.conf.all.bc_forwarding=1
    sudo sysctl -w net.ipv4.icmp_echo_ignore_broadcasts=0
    
    # Enable promiscuous and multicast
    sudo ip link set $BRIDGE_NAME multicast on
    sudo ip link set $BRIDGE_NAME promisc on
    
    # Add iptables rules for broadcast forwarding
    sudo iptables -I FORWARD -i $BRIDGE_NAME -o $BRIDGE_NAME -d 255.255.255.255/32 -j ACCEPT
    sudo iptables -I FORWARD -i $BRIDGE_NAME -o $BRIDGE_NAME -d 172.20.255.255/32 -j ACCEPT
    sudo iptables -I INPUT -i $BRIDGE_NAME -d 255.255.255.255/32 -j ACCEPT
    sudo iptables -I INPUT -i $BRIDGE_NAME -d 172.20.255.255/32 -j ACCEPT
    
    echo -e "${GREEN}✓${NC} Bridge configured for broadcast"
fi

# Test connectivity
echo -e "\n${YELLOW}4. Testing network connectivity...${NC}"

# Test ping
echo -n "Ping test: "
sudo podman exec sc-lan-host ping -c 1 -W 1 $JOIN_IP > /dev/null 2>&1 && \
    echo -e "${GREEN}Host->Join OK${NC}" || \
    echo -e "${RED}Host->Join FAIL${NC}"

# Test UDP broadcast with socat
echo -e "\n${YELLOW}5. Testing UDP broadcast...${NC}"

# Start a UDP listener on host
sudo podman exec -d sc-lan-host bash -c "nc -ulp 6111 > /app/logs/udp-received.txt 2>&1"

# Send broadcast from join
echo "Sending UDP broadcast from JOIN container..."
sudo podman exec sc-lan-join bash -c "echo 'BROADCAST_TEST' | socat - UDP-DATAGRAM:255.255.255.255:6111,broadcast" 2>/dev/null || \
sudo podman exec sc-lan-join bash -c "echo 'BROADCAST_TEST' | nc -u -b 255.255.255.255 6111" 2>/dev/null

sleep 2

# Check if broadcast was received
if sudo podman exec sc-lan-host cat /app/logs/udp-received.txt 2>/dev/null | grep -q "BROADCAST_TEST"; then
    echo -e "${GREEN}✓ UDP broadcast working!${NC}"
else
    echo -e "${RED}✗ UDP broadcast not received${NC}"
    
    # Try subnet broadcast
    echo "Trying subnet broadcast (172.20.255.255)..."
    sudo podman exec sc-lan-join bash -c "echo 'SUBNET_BROADCAST' | socat - UDP-DATAGRAM:172.20.255.255:6111,broadcast" 2>/dev/null
    sleep 1
    if sudo podman exec sc-lan-host cat /app/logs/udp-received.txt 2>/dev/null | grep -q "SUBNET_BROADCAST"; then
        echo -e "${GREEN}✓ Subnet broadcast working!${NC}"
    fi
fi

# Monitor traffic
echo -e "\n${YELLOW}6. Monitoring StarCraft network traffic...${NC}"
echo "Monitoring for 15 seconds..."
echo ""

# Check container status
echo -e "${BLUE}Container Status:${NC}"
sudo podman exec sc-lan-host pgrep -x "StarCraft.exe" > /dev/null && \
    echo -e "  ${GREEN}✓${NC} StarCraft running on HOST" || \
    echo -e "  ${RED}✗${NC} StarCraft not running on HOST"
    
sudo podman exec sc-lan-join pgrep -x "StarCraft.exe" > /dev/null && \
    echo -e "  ${GREEN}✓${NC} StarCraft running on JOIN" || \
    echo -e "  ${RED}✗${NC} StarCraft not running on JOIN"

echo ""
echo -e "${BLUE}VNC Access:${NC}"
echo "  Host: vncviewer localhost:5900"
echo "  Join: vncviewer localhost:5901"
echo ""
echo -e "${BLUE}Instructions:${NC}"
echo "1. Connect via VNC to both containers"
echo "2. In HOST: Multiplayer -> Local Area Network -> Create Game"
echo "3. In JOIN: Multiplayer -> Local Area Network -> Join (should see the game)"
echo ""

# Show some recent logs
echo -e "${BLUE}Recent container logs:${NC}"
echo -e "${YELLOW}HOST:${NC}"
sudo podman logs --tail 5 sc-lan-host 2>&1 | sed 's/^/  /'
echo -e "${YELLOW}JOIN:${NC}"
sudo podman logs --tail 5 sc-lan-join 2>&1 | sed 's/^/  /'

echo ""
echo -e "${GREEN}Setup complete!${NC} Containers are running."
echo "Press Ctrl+C to stop and clean up."
echo ""

# Monitor network traffic in real-time
echo -e "${BLUE}Live network monitor (UDP 6111/6112):${NC}"
(
    sudo podman exec sc-lan-host tcpdump -i eth0 -n 'udp port 6111 or udp port 6112' 2>/dev/null | while read line; do
        echo -e "${GREEN}[HOST]${NC} $line"
    done
) &
HOST_MON=$!

(
    sudo podman exec sc-lan-join tcpdump -i eth0 -n 'udp port 6111 or udp port 6112' 2>/dev/null | while read line; do
        echo -e "${YELLOW}[JOIN]${NC} $line"
    done
) &
JOIN_MON=$!

# Keep running until interrupted
while true; do
    sleep 10
done
