#!/bin/bash

# Internal network analysis script
# Analyzes captured network debugging data

set -e

DEBUG_DIR=${1:-/debug_logs}
TIMESTAMP=${2:-$(date +%Y%m%d_%H%M%S)}

echo "=== Network Debug Analysis ==="
echo "Debug directory: $DEBUG_DIR"
echo "Timestamp filter: $TIMESTAMP"

if [ ! -d "$DEBUG_DIR" ]; then
    echo "Debug directory not found: $DEBUG_DIR"
    exit 1
fi

ANALYSIS_LOG="${DEBUG_DIR}/analysis_${TIMESTAMP}.txt"

echo "=== Network Debug Analysis Report ===" > "$ANALYSIS_LOG"
echo "Generated: $(date)" >> "$ANALYSIS_LOG"
echo "" >> "$ANALYSIS_LOG"

# Find relevant log files
STRACE_FILES=$(find "$DEBUG_DIR" -name "strace_network_*.log" 2>/dev/null || true)
TCPDUMP_FILES=$(find "$DEBUG_DIR" -name "tcpdump_*.pcap" 2>/dev/null || true)
NETSTAT_FILES=$(find "$DEBUG_DIR" -name "netstat_*.log" 2>/dev/null || true)
SUMMARY_FILES=$(find "$DEBUG_DIR" -name "debug_summary_*.log" 2>/dev/null || true)

echo "=== Available Debug Files ===" >> "$ANALYSIS_LOG"
echo "Strace files: $STRACE_FILES" >> "$ANALYSIS_LOG"
echo "Packet capture files: $TCPDUMP_FILES" >> "$ANALYSIS_LOG"
echo "Network status files: $NETSTAT_FILES" >> "$ANALYSIS_LOG"
echo "Summary files: $SUMMARY_FILES" >> "$ANALYSIS_LOG"
echo "" >> "$ANALYSIS_LOG"

# Analyze strace files
if [ -n "$STRACE_FILES" ]; then
    echo "=== Strace Analysis ===" >> "$ANALYSIS_LOG"
    for file in $STRACE_FILES; do
        if [ -f "$file" ]; then
            echo "File: $file" >> "$ANALYSIS_LOG"
            echo "Size: $(wc -l < "$file" 2>/dev/null) lines" >> "$ANALYSIS_LOG"
            
            # Count network system calls
            echo "Network system calls:" >> "$ANALYSIS_LOG"
            grep -E "(socket|bind|listen|connect|accept|send|recv|sendto|recvfrom)" "$file" 2>/dev/null | \
                cut -d'(' -f1 | sort | uniq -c | sort -rn >> "$ANALYSIS_LOG" 2>/dev/null || \
                echo "  No network syscalls found" >> "$ANALYSIS_LOG"
            
            # Look for StarCraft ports
            echo "StarCraft port activity (6111-6119):" >> "$ANALYSIS_LOG"
            grep -E "611[1-9]" "$file" 2>/dev/null | head -10 >> "$ANALYSIS_LOG" || \
                echo "  No StarCraft port activity found" >> "$ANALYSIS_LOG"
                
            echo "" >> "$ANALYSIS_LOG"
        fi
    done
else
    echo "=== Strace Analysis ===" >> "$ANALYSIS_LOG"
    echo "No strace files found" >> "$ANALYSIS_LOG"
    echo "" >> "$ANALYSIS_LOG"
fi

# Analyze packet captures
if [ -n "$TCPDUMP_FILES" ] && command -v tshark >/dev/null 2>&1; then
    echo "=== Packet Capture Analysis ===" >> "$ANALYSIS_LOG"
    for file in $TCPDUMP_FILES; do
        if [ -f "$file" ]; then
            echo "File: $file" >> "$ANALYSIS_LOG"
            echo "Size: $(stat -c%s "$file" 2>/dev/null) bytes" >> "$ANALYSIS_LOG"
            
            # Count packets
            PACKET_COUNT=$(tshark -r "$file" -T fields -e frame.number 2>/dev/null | wc -l || echo "0")
            echo "Total packets: $PACKET_COUNT" >> "$ANALYSIS_LOG"
            
            if [ "$PACKET_COUNT" -gt 0 ]; then
                echo "Protocol distribution:" >> "$ANALYSIS_LOG"
                tshark -r "$file" -T fields -e _ws.col.Protocol 2>/dev/null | \
                    sort | uniq -c | sort -rn >> "$ANALYSIS_LOG" 2>/dev/null || true
                    
                echo "Port distribution:" >> "$ANALYSIS_LOG"
                tshark -r "$file" -T fields -e tcp.port -e udp.port 2>/dev/null | \
                    tr '\t' '\n' | grep -v '^$' | sort | uniq -c | sort -rn | head -10 >> "$ANALYSIS_LOG" 2>/dev/null || true
            fi
            echo "" >> "$ANALYSIS_LOG"
        fi
    done
else
    echo "=== Packet Capture Analysis ===" >> "$ANALYSIS_LOG"
    if [ -z "$TCPDUMP_FILES" ]; then
        echo "No packet capture files found" >> "$ANALYSIS_LOG"
    else
        echo "tshark not available for packet analysis" >> "$ANALYSIS_LOG"
        for file in $TCPDUMP_FILES; do
            echo "File: $file ($(stat -c%s "$file" 2>/dev/null) bytes)" >> "$ANALYSIS_LOG"
        done
    fi
    echo "" >> "$ANALYSIS_LOG"
fi

# Analyze network status files
if [ -n "$NETSTAT_FILES" ]; then
    echo "=== Network Status Analysis ===" >> "$ANALYSIS_LOG"
    for file in $NETSTAT_FILES; do
        if [ -f "$file" ]; then
            echo "File: $file" >> "$ANALYSIS_LOG"
            
            # Find listening ports
            echo "Listening ports:" >> "$ANALYSIS_LOG"
            grep "LISTEN" "$file" 2>/dev/null | awk '{print $4}' | sort -u >> "$ANALYSIS_LOG" || \
                echo "  No listening ports found" >> "$ANALYSIS_LOG"
                
            # Find StarCraft ports
            echo "StarCraft ports (6111-6119):" >> "$ANALYSIS_LOG"
            grep -E "611[1-9]" "$file" 2>/dev/null | head -5 >> "$ANALYSIS_LOG" || \
                echo "  No StarCraft ports found" >> "$ANALYSIS_LOG"
                
            echo "" >> "$ANALYSIS_LOG"
        fi
    done
else
    echo "=== Network Status Analysis ===" >> "$ANALYSIS_LOG"
    echo "No network status files found" >> "$ANALYSIS_LOG"
    echo "" >> "$ANALYSIS_LOG"
fi

echo "=== Analysis Complete ===" >> "$ANALYSIS_LOG"
echo "Report saved to: $ANALYSIS_LOG"

# Display summary on stdout
echo ""
echo "Analysis complete. Report saved to: $ANALYSIS_LOG"
echo ""
echo "Quick summary:"
if [ -n "$STRACE_FILES" ]; then
    echo "- Strace files: $(echo $STRACE_FILES | wc -w)"
fi
if [ -n "$TCPDUMP_FILES" ]; then
    echo "- Packet captures: $(echo $TCPDUMP_FILES | wc -w)"
fi
if [ -n "$NETSTAT_FILES" ]; then
    echo "- Network status logs: $(echo $NETSTAT_FILES | wc -w)"
fi
