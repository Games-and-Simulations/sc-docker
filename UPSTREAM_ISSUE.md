# Issue: StarCraft LAN Discovery Fails in Docker Due to UDP Broadcast Limitations

## Summary
StarCraft: Brood War's LAN discovery mechanism relies on UDP broadcasts to 255.255.255.255 (global broadcast) on ports 6111-6112, which are blocked by Docker's bridge networking. This prevents containers from discovering each other for LAN games, even when on the same Docker network.

## Problem Description
When running multiple StarCraft instances in Docker containers for bot development/testing, the game's LAN discovery fails with "Unable to initialize network provider" errors. This occurs because:

1. StarCraft uses global UDP broadcasts (255.255.255.255) for LAN game discovery
2. Docker bridge networks block global broadcasts for security/isolation
3. Subnet broadcasts (e.g., 172.18.255.255) work but StarCraft doesn't use them

## Testing Performed

### Network Types Tested
- **Bridge networks** (default and custom): Global broadcasts blocked
- **Host network**: Works but loses container isolation, not suitable for multi-container setups
- **Macvlan**: Still blocks global broadcasts between containers

### UDP Broadcast Test Results
Using debug containers with manual UDP testing tools:

```bash
# Container 1: UDP listener on port 6111
docker exec scdbg1 ncat -ulkp 6111

# Container 2: Send broadcasts
docker exec scdbg2 echo "TEST" | socat - UDP-DATAGRAM:255.255.255.255:6111,broadcast
# Result: NOT received

docker exec scdbg2 echo "TEST" | socat - UDP-DATAGRAM:172.18.255.255:6111,broadcast  
# Result: Received successfully
```

## Current Workarounds

### 1. UDP Relay Scripts (Partial Solution)
Created UDP relay scripts that retransmit global broadcasts as subnet broadcasts:
```bash
# docker/scripts/debug/DEBUG_udp_relay.sh
socat -u UDP4-RECVFROM:6111,broadcast,fork,so-bindtodevice=eth0 \
         UDP4-DATAGRAM:172.18.255.255:6111,broadcast,so-bindtodevice=eth0
```

**Limitations:**
- Requires manual start in each container
- Port conflicts when multiple containers relay
- Doesn't fully solve discovery issues

### 2. Debug Mode
Added comprehensive debugging tools to analyze network traffic:
- tcpdump, ncat, socat for packet analysis
- Manual UDP test scripts
- Detailed logging of network failures

## Proposed Solutions

### 1. Short-term: Improved UDP Relay
- Implement a single relay service on the host that forwards broadcasts to all containers
- Avoid port conflicts by having only one relay instance
- Could use iptables/ebtables rules for more efficient forwarding

### 2. Long-term: BWAPI Modification
- Modify BWAPI to support unicast-based discovery
- Add configuration option for explicit peer IP addresses
- Implement a discovery service that containers can register with

### 3. Alternative: Different Container Runtime
- Investigate if Podman or other runtimes handle broadcasts differently
- Consider using network namespaces directly without containerization for LAN games

## Impact
This issue affects anyone trying to run multiple StarCraft bots in containers for:
- Tournament systems
- Bot development and testing
- Automated gameplay analysis
- Multi-agent reinforcement learning

## Files Changed in Investigation
- `docker/dockerfiles/dbg.dockerfile` - Added debugging tools
- `docker/scripts/debug/` - UDP relay and test scripts
- `scbw/docker_utils.py` - Runtime detection improvements
- `DEBUG.md` - Comprehensive debugging documentation
- `NETWORK_FINDINGS.md` - Detailed analysis of the issue

## Environment
- Docker version: 27.2.0
- Host OS: Arch Linux
- Network driver: bridge
- Container base: Wine with StarCraft: Brood War 1.16.1

## Related Issues
This may be related to similar issues with other legacy games that use UDP broadcasts for LAN discovery.

## Request for Input
1. Has anyone successfully solved UDP broadcast forwarding in Docker for legacy applications?
2. Would the project accept a PR that adds a host-based UDP relay service?
3. Is modifying BWAPI for unicast discovery feasible?

## Reproducible Test Case
```bash
# Build debug images
./docker/build_images.sh

# Start two debug containers
docker run -d --name sc1 --network sc_net starcraft:dbg
docker run -d --name sc2 --network sc_net starcraft:dbg

# Test UDP broadcast
docker exec sc1 bash -c 'ncat -ulkp 6111 > /tmp/received.txt &'
docker exec sc2 bash -c 'echo "HELLO" | socat - UDP-DATAGRAM:255.255.255.255:6111,broadcast'
docker exec sc1 cat /tmp/received.txt
# Expected: "HELLO" received
# Actual: Nothing received
```

## Acknowledgments
Thanks to the sc-docker maintainers for the excellent bot development framework. This investigation was conducted to improve the LAN multiplayer capabilities of the system.
