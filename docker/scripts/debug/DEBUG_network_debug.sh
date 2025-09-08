#!/bin/bash

# Internal network debugging script - runs inside the container
# This script automatically finds StarCraft processes and traces network activity

DEBUG_LOG_DIR="/debug_logs"
TIMEOUT_SECONDS="${1:-120}"  # Default 2 minutes

echo "Starting internal network debugging..."
echo "Timeout: $TIMEOUT_SECONDS seconds"
echo "Debug logs will be saved to: $DEBUG_LOG_DIR"

mkdir -p "$DEBUG_LOG_DIR"

# Function to cleanup background processes
cleanup() {
    echo "Cleaning up debugging processes..."
    pkill -f strace 2>/dev/null || true
    pkill -f tcpdump 2>/dev/null || true
    jobs -p | xargs -r kill 2>/dev/null || true
    wait 2>/dev/null
}

trap cleanup EXIT

# Wait for StarCraft to start
echo "Waiting for StarCraft processes to start..."
local wait_count=0
while [ $wait_count -lt 60 ]; do  # Wait up to 1 minute
    starcraft_pids=$(pgrep -f "StarCraft.*exe" 2>/dev/null || true)
    if [ -n "$starcraft_pids" ]; then
        echo "StarCraft processes found: $starcraft_pids"
        break
    fi
    sleep 1
    ((wait_count++))
done

if [ -z "$starcraft_pids" ]; then
    echo "No StarCraft processes found after 60 seconds, continuing anyway..."
fi

# Get system info
echo "=== Container Network Info ===" > "$DEBUG_LOG_DIR/container_network_info.txt"
ip addr show >> "$DEBUG_LOG_DIR/container_network_info.txt" 2>/dev/null
echo "" >> "$DEBUG_LOG_DIR/container_network_info.txt"

echo "=== Container Processes ===" >> "$DEBUG_LOG_DIR/container_processes.txt"
ps aux >> "$DEBUG_LOG_DIR/container_processes.txt" 2>/dev/null
echo "" >> "$DEBUG_LOG_DIR/container_processes.txt"

echo "=== Container UDP Sockets ===" >> "$DEBUG_LOG_DIR/container_sockets.txt"
ss -ulnp >> "$DEBUG_LOG_DIR/container_sockets.txt" 2>/dev/null
echo "" >> "$DEBUG_LOG_DIR/container_sockets.txt"

# Start network packet capture
echo "Starting network packet capture..."
tcpdump -i eth0 -w "$DEBUG_LOG_DIR/container_traffic.pcap" &
TCPDUMP_PID=$!

# Start strace on all StarCraft-related processes
echo "Starting strace on StarCraft processes..."
for pid in $starcraft_pids; do
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        echo "Starting strace on PID $pid"
        strace -p "$pid" \
            -e trace=network,socket,bind,listen,connect,accept,sendto,recvfrom,setsockopt,getsockopt \
            -o "$DEBUG_LOG_DIR/strace_starcraft_$pid.log" \
            2>/dev/null &
    fi
done

# Also trace wineserver if present
wineserver_pid=$(pgrep wineserver 2>/dev/null || true)
if [ -n "$wineserver_pid" ]; then
    echo "Starting strace on wineserver PID $wineserver_pid"
    strace -p "$wineserver_pid" \
        -e trace=network,socket,bind,listen,connect,accept,sendto,recvfrom,setsockopt,getsockopt \
        -o "$DEBUG_LOG_DIR/strace_wineserver_$wineserver_pid.log" \
        2>/dev/null &
fi

# Monitor for new processes that might start later
echo "Monitoring for new StarCraft processes..."
(
    while [ $SECONDS -lt $TIMEOUT_SECONDS ]; do
        new_pids=$(pgrep -f "StarCraft.*exe" 2>/dev/null || true)
        for pid in $new_pids; do
            if [ -n "$pid" ] && ! pgrep -f "strace.*$pid" >/dev/null 2>&1; then
                echo "New StarCraft process detected: PID $pid"
                strace -p "$pid" \
                    -e trace=network,socket,bind,listen,connect,accept,sendto,recvfrom,setsockopt,getsockopt \
                    -o "$DEBUG_LOG_DIR/strace_starcraft_new_$pid.log" \
                    2>/dev/null &
            fi
        done
        sleep 5
    done
) &

# Wait for the timeout
echo "Debugging for $TIMEOUT_SECONDS seconds..."
sleep "$TIMEOUT_SECONDS"

# Stop tcpdump
if [ -n "$TCPDUMP_PID" ]; then
    kill "$TCPDUMP_PID" 2>/dev/null || true
fi

# Final status
echo "=== Final Container UDP Sockets ===" >> "$DEBUG_LOG_DIR/container_sockets.txt"
ss -ulnp >> "$DEBUG_LOG_DIR/container_sockets.txt" 2>/dev/null

echo "=== Final Container Processes ===" >> "$DEBUG_LOG_DIR/container_processes.txt"
ps aux >> "$DEBUG_LOG_DIR/container_processes.txt" 2>/dev/null

echo "Internal network debugging complete."
echo "Log files created:"
ls -la "$DEBUG_LOG_DIR/" 2>/dev/null || true

# Create a summary
echo "=== Network Debugging Summary ===" > "$DEBUG_LOG_DIR/summary.txt"
echo "Container: $(hostname)" >> "$DEBUG_LOG_DIR/summary.txt"
echo "Debug session: $(date)" >> "$DEBUG_LOG_DIR/summary.txt"
echo "Duration: $TIMEOUT_SECONDS seconds" >> "$DEBUG_LOG_DIR/summary.txt"
echo "" >> "$DEBUG_LOG_DIR/summary.txt"

echo "StarCraft processes found:" >> "$DEBUG_LOG_DIR/summary.txt"
echo "$starcraft_pids" >> "$DEBUG_LOG_DIR/summary.txt"
echo "" >> "$DEBUG_LOG_DIR/summary.txt"

echo "Strace log files:" >> "$DEBUG_LOG_DIR/summary.txt"
ls -la "$DEBUG_LOG_DIR"/strace_*.log 2>/dev/null >> "$DEBUG_LOG_DIR/summary.txt" || echo "No strace logs created" >> "$DEBUG_LOG_DIR/summary.txt"
