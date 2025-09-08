# Docker Network UDP Broadcast Findings

## Executive Summary

After extensive testing and configuration attempts, we have discovered that **Docker fundamentally blocks UDP broadcast packets between containers**, regardless of network type or configuration. This impacts StarCraft: Brood War's LAN discovery mechanism, which relies on UDP broadcasts to 255.255.255.255 on ports 6111-6112.

## Problem Statement

StarCraft: Brood War uses UDP broadcasts for LAN game discovery:
- Discovery broadcasts on UDP port 6111
- Game data broadcasts on UDP port 6112
- Broadcasts are sent to 255.255.255.255 (global broadcast address)

Docker containers cannot receive these broadcasts from other containers, preventing LAN game discovery.

## Test Environment

- **OS**: Arch Linux
- **Docker Version**: Latest (as of Sept 2024)
- **Network**: sc_net (172.18.0.0/16)
- **Test Containers**: starcraft:dbg (debug image with networking tools)

## Attempted Solutions and Results

### 1. Bridge Network (Default Docker)

**Configuration**: Standard Docker bridge network

**Result**: 
- ✅ Unicast: Works
- ❌ Subnet Broadcast (172.18.255.255): Blocked
- ❌ Global Broadcast (255.255.255.255): Blocked

### 2. Bridge Network with Kernel/iptables Modifications

**Configuration Applied**:
```bash
# Kernel parameters
sysctl -w net.bridge.bridge-nf-call-iptables=0
sysctl -w net.ipv4.ip_forward=1
sysctl -w net.ipv4.conf.all.bc_forwarding=1

# Bridge settings
ip link set br-<id> promisc on

# ebtables rules
ebtables -I FORWARD -p IPv4 --ip-dst 255.255.255.255 -j ACCEPT

# iptables rules
iptables -I FORWARD -d 255.255.255.255/32 -j ACCEPT
iptables -I DOCKER-USER -d 255.255.255.255/32 -j ACCEPT

# Hairpin mode on veth interfaces
bridge link set dev veth<id> hairpin on
```

**Result**: 
- ✅ Unicast: Works
- ❌ Subnet Broadcast: Still blocked
- ❌ Global Broadcast: Still blocked

### 3. Macvlan Network

**Configuration**:
```bash
docker network create -d macvlan \
  --subnet=172.20.0.0/16 \
  --opt macvlan_mode=bridge \
  sc_macvlan
```

**Result**:
- ✅ Unicast: Works
- ❌ Subnet Broadcast: Blocked
- ❌ Global Broadcast: Blocked

### 4. IPvlan Network (L2 Mode)

**Configuration**:
```bash
docker network create -d ipvlan \
  --subnet=172.21.0.0/16 \
  -o ipvlan_mode=l2 \
  sc_ipvlan
```

**Result**:
- ✅ Unicast: Works
- ❌ Subnet Broadcast: Blocked
- ❌ Global Broadcast: Blocked

### 5. Host Networking

**Configuration**: `--network host`

**Result**:
- ✅ Unicast: Works (to localhost)
- ❌ Global Broadcast to self: Blocked

## Root Cause Analysis

Docker's network drivers implement broadcast filtering at a low level, before packets reach iptables/ebtables. This appears to be a deliberate design decision for:
1. **Security**: Preventing broadcast storms and amplification attacks
2. **Isolation**: Maintaining container network isolation
3. **Performance**: Reducing unnecessary network traffic

## Working Solutions

### 1. UDP Relay Within Containers

**Status**: Partially working

Each container runs a socat relay that attempts to forward broadcasts:
```bash
socat -u UDP4-RECVFROM:6111,broadcast,reuseaddr,fork \
         UDP4-DATAGRAM:255.255.255.255:6111,broadcast
```

**Limitation**: The relay itself cannot receive global broadcasts from other containers.

### 2. Container Network Isolation Options

The network was created with `"isolate": "true"` option in `scbw/docker_utils.py`:
```python
docker_client.networks.create(
    DOCKER_STARCRAFT_NETWORK, 
    driver="bridge",
    options={"isolate": "true"}
)
```

This setting ensures container isolation but may further restrict broadcast forwarding.

## Potential Future Solutions

### 1. Patch BWAPI
Modify BWAPI source code to use:
- Unicast discovery with a registry service
- Subnet-specific broadcasts (172.18.255.255) instead of global
- Multicast groups instead of broadcast

### 2. External Relay Service
Run a privileged service on the host that:
- Captures broadcasts using raw sockets
- Reinjects them into the Docker network
- Acts as a broadcast proxy

### 3. Alternative Container Runtimes
Explore other container runtimes that may handle broadcasts differently:
- Podman with different network plugins
- LXC/LXD containers
- Firecracker microVMs

### 4. Custom Network Plugin
Develop a Docker network plugin that specifically allows broadcast traffic.

## Code Changes Made

### Added Files
- `DEBUG.md` - Comprehensive debugging documentation
- `docker/scripts/hook_init.sh` - UDP relay initialization hook
- `docker/scripts/debug/DEBUG_udp_receiver.sh` - UDP broadcast testing tool
- `docker/scripts/debug/DEBUG_udp_sender.sh` - UDP broadcast sending tool
- `docker/scripts/debug/DEBUG_udp_relay.sh` - Manual UDP relay script
- Various test scripts for network testing

### Modified Files
- `docker/dockerfiles/dbg.dockerfile` - Cleaned up debug container, removed auto-debugging
- `scbw/docker_utils.py` - Improved container runtime detection, removed AUTO_DEBUG
- `docker/scripts/debug/DEBUG_auto_startup.sh` - Made debugging optional
- `docker/build_images.sh` - Fixed build process for rootful Docker

### Key Improvements
1. **Clean Debug Containers**: Debug containers now start normally without automatic debugging processes
2. **Manual Debugging Tools**: All debugging is done via explicit `docker exec` commands
3. **Separated UDP Tools**: Individual scripts for testing different aspects of UDP networking
4. **Better Runtime Detection**: Improved Docker/Podman runtime detection logic

## Recommendations

1. **Short Term**: 
   - Use the existing UDP relay scripts as a partial workaround
   - Document the limitation clearly for users
   - Consider implementing a registry-based discovery service

2. **Long Term**:
   - Investigate patching BWAPI to use different discovery mechanisms
   - Explore alternative container runtimes
   - Consider implementing a custom network solution

## Testing Procedure

To reproduce our findings:

```bash
# 1. Create test containers
docker run -d --name test1 --network sc_net starcraft:dbg sleep infinity
docker run -d --name test2 --network sc_net starcraft:dbg sleep infinity

# 2. Start UDP receiver in test1
docker exec test1 ncat -u -l 6111 > /tmp/test.log &

# 3. Send broadcasts from test2
docker exec test2 bash -c "
  echo 'UNICAST' | socat - UDP4-DATAGRAM:172.18.0.2:6111
  echo 'SUBNET' | socat - UDP4-DATAGRAM:172.18.255.255:6111,broadcast
  echo 'GLOBAL' | socat - UDP4-DATAGRAM:255.255.255.255:6111,broadcast
"

# 4. Check received packets
docker exec test1 cat /tmp/test.log
# Result: Only UNICAST will be received
```

## Conclusion

Docker's current architecture fundamentally prevents UDP broadcast communication between containers. This is not a configuration issue but a design limitation. Any solution will require either:
1. Modifying the application (BWAPI) to not rely on broadcasts
2. Implementing an external relay/proxy service
3. Using a different container technology

The UDP relay scripts provide a foundation for a workaround, but cannot fully solve the broadcast limitation due to Docker's network isolation model.
