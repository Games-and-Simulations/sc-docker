#!/bin/bash

# Internal network analysis script
# This script analyzes the captured network debugging data

DEBUG_LOG_DIR="/debug_logs"

if [ ! -d "$DEBUG_LOG_DIR" ]; then
    echo "Debug log directory not found: $DEBUG_LOG_DIR"
    exit 1
fi

echo "Analyzing network debugging data in $DEBUG_LOG_DIR..."

# Create analysis report
ANALYSIS_FILE="$DEBUG_LOG_DIR/network_analysis.txt"

echo "=== StarCraft Container Network Analysis ===" > "$ANALYSIS_FILE"
echo "Analysis performed at: $(date)" >> "$ANALYSIS_FILE"
echo "Container: $(hostname)" >> "$ANALYSIS_FILE"
echo "" >> "$ANALYSIS_FILE"

# Analyze strace logs
echo "=== STRACE ANALYSIS ===" >> "$ANALYSIS_FILE"
strace_files=$(ls "$DEBUG_LOG_DIR"/strace_*.log 2>/dev/null || true)

if [ -n "$strace_files" ]; then
    for strace_file in $strace_files; do
        echo "--- Analysis of $strace_file ---" >> "$ANALYSIS_FILE"
        
        # Count different types of network calls
        echo "Network system call counts:" >> "$ANALYSIS_FILE"
        grep -E "socket|bind|listen|connect|accept|sendto|recvfrom" "$strace_file" 2>/dev/null | \
            cut -d'(' -f1 | sort | uniq -c | sort -nr >> "$ANALYSIS_FILE" 2>/dev/null || echo "No network calls found" >> "$ANALYSIS_FILE"
        
        # Look for UDP traffic on StarCraft ports
        echo "" >> "$ANALYSIS_FILE"
        echo "UDP traffic on StarCraft ports (6111-6119):" >> "$ANALYSIS_FILE"
        grep -E "sendto.*6111|sendto.*6112|sendto.*6113|sendto.*6114|sendto.*6115|sendto.*6116|sendto.*6117|sendto.*6118|sendto.*6119" "$strace_file" 2>/dev/null >> "$ANALYSIS_FILE" || echo "No UDP sendto calls on StarCraft ports" >> "$ANALYSIS_FILE"
        
        echo "" >> "$ANALYSIS_FILE"
        echo "UDP receive on StarCraft ports:" >> "$ANALYSIS_FILE"
        grep -E "recvfrom.*6111|recvfrom.*6112|recvfrom.*6113|recvfrom.*6114|recvfrom.*6115|recvfrom.*6116|recvfrom.*6117|recvfrom.*6118|recvfrom.*6119" "$strace_file" 2>/dev/null >> "$ANALYSIS_FILE" || echo "No UDP recvfrom calls on StarCraft ports" >> "$ANALYSIS_FILE"
        
        # Look for socket creation
        echo "" >> "$ANALYSIS_FILE"
        echo "Socket creation:" >> "$ANALYSIS_FILE"
        grep "socket(" "$strace_file" 2>/dev/null >> "$ANALYSIS_FILE" || echo "No socket creation calls" >> "$ANALYSIS_FILE"
        
        # Look for bind calls
        echo "" >> "$ANALYSIS_FILE"
        echo "Bind calls:" >> "$ANALYSIS_FILE"
        grep "bind(" "$strace_file" 2>/dev/null >> "$ANALYSIS_FILE" || echo "No bind calls" >> "$ANALYSIS_FILE"
        
        echo "" >> "$ANALYSIS_FILE"
    done
else
    echo "No strace log files found" >> "$ANALYSIS_FILE"
fi

# Analyze network interface info
echo "=== NETWORK INTERFACE ANALYSIS ===" >> "$ANALYSIS_FILE"
if [ -f "$DEBUG_LOG_DIR/container_network_info.txt" ]; then
    echo "Container IP addresses:" >> "$ANALYSIS_FILE"
    grep -E "inet [0-9]" "$DEBUG_LOG_DIR/container_network_info.txt" >> "$ANALYSIS_FILE" 2>/dev/null || echo "No IP addresses found" >> "$ANALYSIS_FILE"
else
    echo "Network info file not found" >> "$ANALYSIS_FILE"
fi

# Analyze socket status
echo "" >> "$ANALYSIS_FILE"
echo "=== SOCKET ANALYSIS ===" >> "$ANALYSIS_FILE"
if [ -f "$DEBUG_LOG_DIR/container_sockets.txt" ]; then
    echo "UDP sockets on StarCraft ports:" >> "$ANALYSIS_FILE"
    grep -E ":611[1-9]" "$DEBUG_LOG_DIR/container_sockets.txt" >> "$ANALYSIS_FILE" 2>/dev/null || echo "No UDP sockets on StarCraft ports" >> "$ANALYSIS_FILE"
    
    echo "" >> "$ANALYSIS_FILE"
    echo "mDNS sockets (port 5353):" >> "$ANALYSIS_FILE"
    grep ":5353" "$DEBUG_LOG_DIR/container_sockets.txt" >> "$ANALYSIS_FILE" 2>/dev/null || echo "No mDNS sockets" >> "$ANALYSIS_FILE"
else
    echo "Socket info file not found" >> "$ANALYSIS_FILE"
fi

# Analyze packet capture if tshark is available
echo "" >> "$ANALYSIS_FILE"
echo "=== PACKET CAPTURE ANALYSIS ===" >> "$ANALYSIS_FILE"
if [ -f "$DEBUG_LOG_DIR/container_traffic.pcap" ] && command -v tshark >/dev/null 2>&1; then
    echo "Packet capture summary:" >> "$ANALYSIS_FILE"
    tshark -r "$DEBUG_LOG_DIR/container_traffic.pcap" -q -z io,stat,0 >> "$ANALYSIS_FILE" 2>/dev/null || echo "Failed to analyze packet capture" >> "$ANALYSIS_FILE"
    
    echo "" >> "$ANALYSIS_FILE"
    echo "UDP traffic on StarCraft ports:" >> "$ANALYSIS_FILE"
    tshark -r "$DEBUG_LOG_DIR/container_traffic.pcap" -Y "udp.port >= 6111 and udp.port <= 6119" >> "$ANALYSIS_FILE" 2>/dev/null || echo "No UDP traffic on StarCraft ports" >> "$ANALYSIS_FILE"
    
    echo "" >> "$ANALYSIS_FILE"
    echo "mDNS traffic:" >> "$ANALYSIS_FILE"
    tshark -r "$DEBUG_LOG_DIR/container_traffic.pcap" -Y "mdns" >> "$ANALYSIS_FILE" 2>/dev/null || echo "No mDNS traffic" >> "$ANALYSIS_FILE"
elif [ -f "$DEBUG_LOG_DIR/container_traffic.pcap" ]; then
    echo "Packet capture file exists but tshark not available for analysis" >> "$ANALYSIS_FILE"
    ls -la "$DEBUG_LOG_DIR/container_traffic.pcap" >> "$ANALYSIS_FILE"
else
    echo "No packet capture file found" >> "$ANALYSIS_FILE"
fi

# Show processes that were running
echo "" >> "$ANALYSIS_FILE"
echo "=== PROCESS ANALYSIS ===" >> "$ANALYSIS_FILE"
if [ -f "$DEBUG_LOG_DIR/container_processes.txt" ]; then
    echo "StarCraft-related processes:" >> "$ANALYSIS_FILE"
    grep -E "StarCraft|wineserver|wine|mDNS" "$DEBUG_LOG_DIR/container_processes.txt" >> "$ANALYSIS_FILE" 2>/dev/null || echo "No StarCraft-related processes found" >> "$ANALYSIS_FILE"
else
    echo "Process info file not found" >> "$ANALYSIS_FILE"
fi

echo "" >> "$ANALYSIS_FILE"
echo "=== ANALYSIS COMPLETE ===" >> "$ANALYSIS_FILE"

echo "Network analysis complete. Results saved to: $ANALYSIS_FILE"
echo ""
echo "=== SUMMARY ==="
cat "$ANALYSIS_FILE"
