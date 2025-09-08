# Using sc-docker with Podman

This document describes how to use sc-docker with Podman as a Docker alternative.

## Overview

Podman is a daemonless container runtime that provides a Docker-compatible command-line interface. While sc-docker is primarily designed for Docker, it can work with Podman with some considerations.

## Installation

### Linux (Rootless Podman)

1. Install Podman:
```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y podman

# Fedora/RHEL/CentOS
sudo dnf install -y podman

# Arch Linux
sudo pacman -S podman
```

2. Enable Docker compatibility:
```bash
# Create docker command alias
sudo ln -s /usr/bin/podman /usr/bin/docker

# OR use podman-docker package (if available)
sudo apt-get install podman-docker  # Ubuntu/Debian
sudo dnf install podman-docker      # Fedora
```

3. Enable Podman socket for Docker API compatibility:
```bash
systemctl --user enable --now podman.socket
export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/podman/podman.sock
```

4. Build sc-docker images:
```bash
cd docker
./build_images.sh
```

## Network Configuration

### Rootless Networking Limitations

Rootless Podman uses different network backends that have limitations for LAN game discovery:

- **pasta** (default): NAT without L2 broadcast support
- **slirp4netns**: Similar NAT limitations
- **host**: Full network access but shares host network namespace

### LAN Multiplayer Workarounds

Since rootless networking doesn't support UDP broadcast for game discovery, use these alternatives:

#### Option 1: Direct IP Connection (Recommended)
Use bwheadless's `--lan-sendto` flag to directly connect to a specific IP:

```bash
# Host a game on your machine
scbw.play --bots "HostBot" --headless

# Join from container (replace IP with your host IP)
podman run -d --name sc-joiner \
  --network pasta \
  --cap-add NET_RAW --cap-add NET_ADMIN --cap-add NET_BIND_SERVICE \
  -v "$HOME/.scbw/maps:/app/sc/maps:ro" \
  starcraft:game \
  /app/play_human.sh \
    --name JoinBot --race T \
    --lan --join --lan-sendto 192.168.1.100:6112
```

#### Option 2: Rootful Podman (Full LAN Support)
If you need full LAN discovery, use rootful Podman:

```bash
sudo podman network create sc_net --driver bridge
sudo scbw.play --bots "Bot1" "Bot2"
```

#### Option 3: Host Network (Development Only)
For testing, you can use host networking:

```bash
podman run --network host ...
```

## Known Issues and Solutions

### 1. Permission Errors
If you encounter permission errors with volume mounts:

```bash
# Fix ownership of .scbw directory
podman unshare chown -R $(id -u):$(id -g) ~/.scbw

# Or use :z flag for SELinux systems
-v "$HOME/.scbw/maps:/app/sc/maps:ro,z"
```

### 2. Docker Socket Not Found
If scbw.play can't find Docker:

```bash
# Start podman socket
systemctl --user start podman.socket

# Set environment variable
export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/podman/podman.sock

# Install podman-docker compatibility package
sudo apt-get install podman-docker
```

### 3. Network Creation Fails
If network creation fails in rootless mode:

```bash
# Use podman directly to create network
podman network create sc_net

# Or switch to rootful
sudo podman network create sc_net
```

## Debugging

### Enable Debug Mode
```bash
scbw.play --bots "Bot1" "Bot2" --debug
```

### Check Container Logs
```bash
podman logs <container-name>
podman exec <container-name> cat /app/logs/game.log
```

### Network Debugging
```bash
# Check network configuration
podman network inspect sc_net

# Test connectivity between containers
podman exec -it container1 ping container2

# Capture network traffic
podman exec container tcpdump -i any -w /tmp/capture.pcap
```

## Performance Tuning

### CPU and Memory Limits
```bash
scbw.play --bots "Bot1" "Bot2" \
  --mem_limit "512m" \
  --nano_cpus 1000000000  # 1 CPU
```

### Storage Driver
For better performance, use overlay storage driver:

```bash
# Check current driver
podman info | grep -i storage

# Configure overlay (in ~/.config/containers/storage.conf)
[storage]
driver = "overlay"
```

## Compatibility Notes

### Tested Configurations
- ✅ Arch Linux with Podman 4.x
- ✅ Ubuntu 22.04 with Podman 3.4+
- ✅ Fedora 38+ with Podman 4.x

### Feature Support Matrix

| Feature | Docker | Rootless Podman | Rootful Podman |
|---------|--------|-----------------|----------------|
| Bot vs Bot | ✅ | ✅ | ✅ |
| Human vs Bot | ✅ | ⚠️ (Direct IP only) | ✅ |
| LAN Discovery | ✅ | ❌ | ✅ |
| VNC Access | ✅ | ✅ | ✅ |
| Debug Mode | ✅ | ✅ | ✅ |

## Troubleshooting Checklist

1. ✓ Podman installed and running
2. ✓ Docker compatibility enabled (`podman-docker` package or alias)
3. ✓ Podman socket running (`systemctl --user status podman.socket`)
4. ✓ DOCKER_HOST environment variable set
5. ✓ Images built successfully (`podman images | grep starcraft`)
6. ✓ Network created (`podman network ls | grep sc_net`)
7. ✓ Permissions correct on ~/.scbw directory
8. ✓ For LAN games: using --lan-sendto or rootful mode

## Additional Resources

- [Podman Documentation](https://docs.podman.io/)
- [Podman Networking Guide](https://github.com/containers/podman/blob/main/docs/tutorials/basic_networking.md)
- [Docker to Podman Migration](https://docs.podman.io/en/latest/markdown/podman-docker.1.html)
- [sc-docker Issues](https://github.com/Games-and-Simulations/sc-docker/issues)
