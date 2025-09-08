#!/bin/bash

# Internal network debugging script
# Runs network tracing and packet capture inside the StarCraft container

set -e

# Parameters
TIMEOUT=${1:-120}
DEBUG_DIR=${2:-/debug_logs}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=== Internal Network Debugging Started ==="
echo "Timeout: ${TIMEOUT}s"
echo "Debug directory: ${DEBUG_DIR}"
echo "Timestamp: ${TIMESTAMP}"

# Create debug files
mkdir -p "$DEBUG_DIR"
STRACE_LOG="${DEBUG_DIR}/strace_network_${TIMESTAMP}.log"
TCPDUMP_LOG="${DEBUG_DIR}/tcpdump_${TIMESTAMP}.pcap"
NETSTAT_LOG="${DEBUG_DIR}/netstat_${TIMESTAMP}.log"
PROCESSES_LOG="${DEBUG_DIR}/processes_${TIMESTAMP}.log"
SUMMARY_LOG="${DEBUG_DIR}/debug_summary_${TIMESTAMP}.log"

# Function to cleanup background processes
cleanup() {
    echo "Cleaning up debugging processes..."
    jobs -p | xargs -r kill 2>/dev/null || true
    echo "Network debugging cleanup complete"
}
trap cleanup EXIT

# Log initial state
echo "=== Initial System State ===" > "$SUMMARY_LOG"
echo "Container processes:" >> "$SUMMARY_LOG"
ps aux >> "$PROCESSES_LOG" 2>&1

# Wait a bit for StarCraft to start
echo "Waiting 5 seconds for StarCraft processes to start..."
sleep 5

# Find StarCraft processes
STARCRAFT_PIDS=$(pgrep -x StarCraft.exe 2>/dev/null || true)
WINESERVER_PIDS=$(pgrep -x wineserver 2>/dev/null || true)

echo "Found processes:" >> "$SUMMARY_LOG"
echo "  StarCraft.exe PIDs: $STARCRAFT_PIDS" >> "$SUMMARY_LOG"
echo "  wineserver PIDs: $WINESERVER_PIDS" >> "$SUMMARY_LOG"

# Start network packet capture
echo "Starting network packet capture..." >> "$SUMMARY_LOG"
tcpdump -i any -w "$TCPDUMP_LOG" 'port 6111 or port 6112 or port 6113 or port 6114 or port 6115 or port 6116 or port 6117 or port 6118 or port 6119' &
TCPDUMP_PID=$!

# Start network system call tracing for StarCraft processes
if [ -n "$STARCRAFT_PIDS" ]; then
    echo "Starting strace for StarCraft processes: $STARCRAFT_PIDS" >> "$SUMMARY_LOG"
    strace -e trace=network -f -tt -o "$STRACE_LOG" -p $STARCRAFT_PIDS &
    STRACE_PID=$!
else
    echo "No StarCraft processes found for tracing" >> "$SUMMARY_LOG"
fi

# Monitor network connections
echo "Starting network monitoring..." >> "$SUMMARY_LOG"
while [ $SECONDS -lt $TIMEOUT ]; do
    echo "=== Network Status at $(date) ===" >> "$NETSTAT_LOG"
    netstat -tuln >> "$NETSTAT_LOG" 2>&1 || true
    echo "" >> "$NETSTAT_LOG"
    sleep 10
done &
NETSTAT_PID=$!

# Wait for the specified timeout
echo "Running debugging for ${TIMEOUT} seconds..."
sleep $TIMEOUT

# Generate summary
echo "=== Final Network State ===" >> "$SUMMARY_LOG"
echo "Network connections:" >> "$SUMMARY_LOG"
netstat -tuln >> "$SUMMARY_LOG" 2>&1 || true

echo "=== File Sizes ===" >> "$SUMMARY_LOG"
ls -la "$DEBUG_DIR"/*_${TIMESTAMP}.* >> "$SUMMARY_LOG" 2>&1 || true

# Final process check
echo "=== Final Process State ===" >> "$SUMMARY_LOG"
ps aux | grep -E "(StarCraft|wine)" >> "$SUMMARY_LOG" 2>&1 || true

echo "Network debugging completed. Files saved:"
echo "  Strace: $STRACE_LOG"
echo "  Packet capture: $TCPDUMP_LOG"
echo "  Network monitoring: $NETSTAT_LOG"
echo "  Processes: $PROCESSES_LOG"
echo "  Summary: $SUMMARY_LOG"
