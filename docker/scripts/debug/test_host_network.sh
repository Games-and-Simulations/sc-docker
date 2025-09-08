#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}StarCraft LAN Discovery - Host Network Test${NC}"
echo "=============================================="
echo ""
echo -e "${YELLOW}Note: Using host network mode - containers will share host's network stack${NC}"
echo ""

# Configuration
IMAGE="starcraft:game"
MAPS_DIR="$HOME/.scbw/maps"
LOGS_DIR="$HOME/.scbw/logs"
GAMES_DIR="$HOME/.scbw/games"

# Ensure directories exist with proper permissions
mkdir -p "$LOGS_DIR" "$GAMES_DIR"
chmod 777 "$LOGS_DIR" "$GAMES_DIR"

# Clean up existing containers
echo -e "${YELLOW}Cleaning up existing containers...${NC}"
sudo podman stop sc-host-net sc-join-net 2>/dev/null
sudo podman rm sc-host-net sc-join-net 2>/dev/null

# Clean up function
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"
    sudo podman stop sc-host-net sc-join-net 2>/dev/null
    sudo podman rm sc-host-net sc-join-net 2>/dev/null
}

trap cleanup EXIT

# Start HOST container with host networking and proper display
echo -e "\n${YELLOW}1. Starting HOST container (host network, VNC port 5900)...${NC}"
sudo podman run -d \
    --name sc-host-net \
    --network host \
    --cap-add ALL \
    -v "$MAPS_DIR:/app/sc/maps:ro" \
    -v "$LOGS_DIR:/app/logs:rw" \
    -v "$GAMES_DIR:/app/games:rw" \
    -e DISPLAY=:99 \
    $IMAGE \
    bash -c "
        # Kill any existing X server on :99
        pkill -f 'Xvfb :99' || true
        sleep 1
        
        # Start Xvfb with 24-bit color depth for better quality
        Xvfb :99 -screen 0 800x600x24 -ac &
        sleep 2
        
        # Start VNC on port 5900
        x11vnc -forever -nopw -display :99 -rfbport 5900 &
        
        # Configure Wine for better graphics
        export WINEDEBUG=-all
        export WINEPREFIX=/app/wine
        
        # Start StarCraft
        echo 'Starting StarCraft HOST...'
        cd /app/sc
        wine StarCraft.exe &
        
        # Keep container running
        while true; do
            if pgrep -x 'StarCraft.exe' > /dev/null; then
                echo 'StarCraft HOST is running'
            else
                echo 'StarCraft HOST stopped - restarting...'
                cd /app/sc && wine StarCraft.exe &
            fi
            sleep 30
        done
    "

# Wait for first container to start
sleep 5

# Start JOIN container with different VNC port
echo -e "\n${YELLOW}2. Starting JOIN container (host network, VNC port 5901)...${NC}"
sudo podman run -d \
    --name sc-join-net \
    --network host \
    --cap-add ALL \
    -v "$MAPS_DIR:/app/sc/maps:ro" \
    -v "$LOGS_DIR:/app/logs:rw" \
    -v "$GAMES_DIR:/app/games:rw" \
    -e DISPLAY=:98 \
    $IMAGE \
    bash -c "
        # Kill any existing X server on :98
        pkill -f 'Xvfb :98' || true
        sleep 1
        
        # Start Xvfb with 24-bit color depth
        Xvfb :98 -screen 0 800x600x24 -ac &
        sleep 2
        
        # Start VNC on port 5901
        x11vnc -forever -nopw -display :98 -rfbport 5901 &
        
        # Configure Wine for better graphics
        export WINEDEBUG=-all
        export WINEPREFIX=/app/wine
        
        # Start StarCraft
        echo 'Starting StarCraft JOIN...'
        cd /app/sc
        wine StarCraft.exe &
        
        # Keep container running
        while true; do
            if pgrep -x 'StarCraft.exe' > /dev/null; then
                echo 'StarCraft JOIN is running'
            else
                echo 'StarCraft JOIN stopped - restarting...'
                cd /app/sc && wine StarCraft.exe &
            fi
            sleep 30
        done
    "

# Wait for containers to start
sleep 5

# Check status
echo -e "\n${YELLOW}3. Checking container status...${NC}"
sudo podman exec sc-host-net pgrep -x "StarCraft.exe" > /dev/null && \
    echo -e "${GREEN}✓ StarCraft HOST is running${NC}" || \
    echo -e "${RED}✗ StarCraft HOST not running${NC}"
    
sudo podman exec sc-join-net pgrep -x "StarCraft.exe" > /dev/null && \
    echo -e "${GREEN}✓ StarCraft JOIN is running${NC}" || \
    echo -e "${RED}✗ StarCraft JOIN not running${NC}"

echo -e "\n==============================================="
echo -e "${GREEN}SETUP COMPLETE - Host Network Mode${NC}"
echo "==============================================="
echo ""
echo -e "${BLUE}VNC Access (improved 24-bit color):${NC}"
echo "  • Host: vncviewer localhost:5900"
echo "  • Join: vncviewer localhost:5901"
echo ""
echo -e "${BLUE}Network Details:${NC}"
echo "  • Mode: Host networking (shared with host)"
echo "  • Both containers can see each other directly"
echo "  • LAN broadcast should work without issues"
echo ""
echo -e "${BLUE}To test LAN discovery:${NC}"
echo "  1. Connect to HOST via VNC (port 5900)"
echo "  2. Go to: Multiplayer → Local Area Network (UDP)"
echo "  3. Create a game"
echo "  4. Connect to JOIN via VNC (port 5901)"
echo "  5. Go to: Multiplayer → Local Area Network (UDP)"
echo "  6. The game should appear in the list"
echo ""
echo -e "${YELLOW}Note: If this works but bridge mode doesn't, the issue is with bridge broadcast forwarding${NC}"
echo ""
echo "Press Ctrl+C to stop containers"

# Keep script running
while true; do
    sleep 10
done
