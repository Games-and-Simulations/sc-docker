#!/usr/bin/env python3
"""
UDP Broadcast Relay for StarCraft LAN Discovery
Forwards UDP broadcasts between container interfaces on a bridge network
"""

import socket
import sys
import threading
import struct
import time

def create_broadcast_socket(port, interface_ip):
    """Create a socket for receiving broadcasts on a specific interface"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(('', port))
    return sock

def create_send_socket():
    """Create a socket for sending broadcasts"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    return sock

def relay_broadcasts(recv_port, send_port, subnet_broadcast):
    """Relay broadcasts from recv_port to send_port"""
    recv_sock = create_broadcast_socket(recv_port, '0.0.0.0')
    send_sock = create_send_socket()
    
    print(f"Relaying UDP broadcasts on port {recv_port} to {subnet_broadcast}:{send_port}")
    
    while True:
        try:
            data, addr = recv_sock.recvfrom(65535)
            source_ip = addr[0]
            
            # Don't relay our own packets
            if source_ip != '127.0.0.1':
                print(f"Received {len(data)} bytes from {source_ip}:{addr[1]}, relaying to {subnet_broadcast}:{send_port}")
                send_sock.sendto(data, (subnet_broadcast, send_port))
                
                # Also send to specific container IPs if known
                for ip in ['172.20.0.2', '172.20.0.3', '172.20.0.4', '172.20.0.5']:
                    if ip != source_ip:
                        try:
                            send_sock.sendto(data, (ip, send_port))
                        except:
                            pass
        except Exception as e:
            print(f"Error relaying: {e}")
            time.sleep(1)

def main():
    # StarCraft uses UDP ports 6111 (discovery) and 6112 (game)
    subnet_broadcast = '172.20.255.255'
    
    # Create threads for each port
    t1 = threading.Thread(target=relay_broadcasts, args=(6111, 6111, subnet_broadcast))
    t2 = threading.Thread(target=relay_broadcasts, args=(6112, 6112, subnet_broadcast))
    
    t1.daemon = True
    t2.daemon = True
    
    t1.start()
    t2.start()
    
    print("UDP Broadcast Relay running for StarCraft LAN discovery")
    print("Relaying on ports 6111 and 6112")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping relay...")
        sys.exit(0)

if __name__ == "__main__":
    main()
