# StarCraft Docker Debugging Guide

This guide covers the debugging tools and hooks available in the `starcraft:dbg` debug container.

## Overview

The debug container (`starcraft:dbg`) includes all the tools from the base game container plus additional debugging and networking tools. By default, it starts exactly like a normal game container - no automatic debugging processes are launched.

## Available Debugging Tools

### Network Analysis Tools
- `tcpdump` - Network packet capture
- `tshark` - Wireshark command-line tool  
- `socat` - Socket relay and UDP broadcast forwarding
- `ncat` - Network testing and relay tool
- `netstat-nat` - Network connection monitoring
- `lsof` - List open files and network connections
- `iptables` - Firewall and traffic manipulation
- `bridge-utils` - Network bridge management

### System Analysis Tools
- `strace` - System call tracing
- `ltrace` - Library call tracing
- `gdb` - GNU debugger
- `htop` - Process monitoring
- `procps` - Process utilities

### GUI and Display Tools  
- `x11vnc` - VNC server for remote desktop access
- `xvfb` - Virtual framebuffer X server
- `kde-cli-tools` - KDE command-line utilities

## Manual Debugging Scripts

The debug container includes several pre-built scripts that can be run manually via `docker exec`:

### UDP Network Debugging
```bash
# Start UDP broadcast receiver (listens for broadcasts)
/app/scripts/DEBUG_udp_receiver.sh [port] [logfile]

# Send UDP broadcast (tests broadcast sending)
/app/scripts/DEBUG_udp_sender.sh [port] [message] [target]

# Start UDP relay (forwards broadcasts between containers)
/app/scripts/DEBUG_udp_relay.sh [port] [target_broadcast]

# Start automatic UDP relay for LAN discovery (runs in background)
/app/scripts/udp_lan_relay.sh
```

### System Debugging
```bash
# Start comprehensive network debugging
/app/scripts/DEBUG_network_debug.sh [timeout_seconds]

# Start network analysis and packet capture
/app/scripts/DEBUG_network_analysis.sh

# Start automatic debugging (legacy - not recommended)
/app/scripts/DEBUG_auto_startup.sh
```

## Environment Variables

### Network Configuration
- `BWAPI_AUTO_MENU=LAN` - Enable LAN mode (automatically set)
- `BWAPI_LAN_MODE="Local Area Network (UDP)"` - UDP networking mode

### Debug Control (Legacy - No Longer Used)
- Debug containers now start normally by default
- No automatic debugging processes are launched
- All debugging is done via manual `docker exec` commands

## Usage Examples

### Basic Debug Container
```bash
# Start debug container normally (same as game container)
docker run --rm --network sc_net starcraft:dbg /app/play_bot.sh --headless --game TEST --name Bot1 --race Z --lan --host

# Start with VNC access for GUI debugging
docker run --rm --network sc_net -p 5900:5900 starcraft:dbg /app/play_bot.sh --headful
```

### Manual Network Debugging
```bash
# Start debug game normally
scbw.play --bots Bot1 Bot2 --debug

# In another terminal, access running container for debugging
docker exec -it GAME_XXX_0_Bot1 /app/scripts/DEBUG_udp_relay.sh 6111

# Or run broadcast receiver to monitor UDP traffic
docker exec -it GAME_XXX_0_Bot1 /app/scripts/DEBUG_udp_receiver.sh 6111

# Or start comprehensive network debugging
docker exec -it GAME_XXX_0_Bot1 /app/scripts/DEBUG_network_debug.sh 60
```

### Advanced Network Testing
```bash
# Test UDP broadcasts between containers
docker run --rm -it --name debug1 --network sc_net starcraft:dbg bash
# In container: ncat -u -l 6111 > /tmp/udp.log &

docker run --rm -it --name debug2 --network sc_net starcraft:dbg bash  
# In container: echo "TEST" | socat - UDP4-DATAGRAM:255.255.255.255:6111,broadcast
```

## Network Issues and Solutions

### StarCraft LAN Discovery Problems

**Problem**: StarCraft containers can't discover each other for LAN games.

**Root Cause**: Docker bridge networks don't forward global UDP broadcasts (255.255.255.255) between containers by default.

**Solutions**:

1. **Use UDP Relay** (Recommended):
   ```bash
   # In each game container, start the UDP relay
   /app/scripts/udp_lan_relay.sh
   ```

2. **Manual socat Relay**:
   ```bash
   # Forward UDP broadcasts on port 6111 (discovery)
   socat -u UDP4-RECVFROM:6111,broadcast,reuseaddr,fork UDP4-DATAGRAM:255.255.255.255:6111,broadcast &
   
   # Forward UDP broadcasts on port 6112 (game data)  
   socat -u UDP4-RECVFROM:6112,broadcast,reuseaddr,fork UDP4-DATAGRAM:255.255.255.255:6112,broadcast &
   ```

3. **Subnet-specific Broadcasts**:
   ```bash
   # Use Docker network's broadcast address (e.g., 172.18.255.255)
   SUBNET_BROADCAST=$(ip route | grep 'sc_net' | awk '{print $1}' | head -1 | sed 's/0\/16/255.255/')
   socat - UDP4-DATAGRAM:$SUBNET_BROADCAST:6111,broadcast
   ```

### Debugging Port Conflicts

**Problem**: Multiple socat/UDP relay processes binding to the same port.

**Solution**: Kill existing processes before starting new ones:
```bash
pkill socat
pkill ncat
# Then start your debugging tools
```

## Integration with scbw.play

### Normal Debug Mode
```bash
# Starts debug container but behaves like normal game container
scbw.play --bots Bot1 Bot2 --debug
```

### Manual Debugging
```bash
# Start containers with debug image
scbw.play --bots Bot1 Bot2 --debug

# In separate terminals, access the containers
docker exec -it GAME_XXX_0_Bot1 bash
# Run debugging commands manually
```

## Troubleshooting

### No socat Found
If you get "socat not found" in the game container:
- Use `--debug` flag to run with the debug image
- The base `starcraft:game` image doesn't include socat

### UDP Relay Not Working  
1. Check if socat is running: `ps aux | grep socat`
2. Check port bindings: `netstat -ulnp | grep 611`
3. Kill competing processes: `pkill socat`
4. Restart relay: `/app/scripts/udp_lan_relay.sh`

### Network Discovery Issues
1. Check container IPs: `docker exec CONTAINER hostname -I`
2. Test basic connectivity: `docker exec CONTAINER1 ping CONTAINER2_IP`
3. Test UDP broadcasts manually with ncat/socat
4. Check Docker network: `docker network inspect sc_net`

## File Locations

- Debug scripts: `/app/scripts/`
- Debug logs: `/debug_logs/` (when mounted)
- Game logs: `/app/logs/`
- Network configs: `/app/sc/bwapi-data/bwapi.ini`
