#!/bin/bash
# install_bonjour.sh - Install Bonjour Print Services for Wine
# This script installs Apple's Bonjour for Windows inside Wine to enable
# mDNS/Bonjour LAN game discovery for StarCraft

set -e

echo "Installing Bonjour Print Services..."

# Ensure we're running as the starcraft user
if [ "$(whoami)" != "starcraft" ]; then
    echo "This script must be run as the starcraft user"
    exit 1
fi

# Check if BonjourPSSetup.exe exists
if [ ! -f "/home/starcraft/BonjourPSSetup.exe" ]; then
    echo "BonjourPSSetup.exe not found at /home/starcraft/BonjourPSSetup.exe"
    exit 1
fi

# Initialize Wine prefix if not already done
if [ ! -d "/home/starcraft/.wine" ]; then
    echo "Initializing Wine prefix..."
    WINEARCH=win32 WINEPREFIX=/home/starcraft/.wine winecfg /v win7
fi

# Install Bonjour using Wine with silent installation
echo "Running Bonjour installer in Wine..."
cd /home/starcraft
WINEPREFIX=/home/starcraft/.wine wine BonjourPSSetup.exe /S

# Verify installation by checking for mDNSResponder.exe
MDNS_PATH="/home/starcraft/.wine/drive_c/Program Files/Bonjour"
if [ -f "$MDNS_PATH/mDNSResponder.exe" ]; then
    echo "Bonjour installation successful - mDNSResponder.exe found"
    ls -la "$MDNS_PATH/"
else
    echo "Bonjour installation may have failed - mDNSResponder.exe not found"
    echo "Checking alternative locations..."
    find /home/starcraft/.wine -name "mDNSResponder.exe" -type f 2>/dev/null || true
fi

# Check Wine registry for Bonjour service entries
echo "Checking Wine registry for Bonjour services..."
WINEPREFIX=/home/starcraft/.wine wine reg query "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\Bonjour Service" 2>/dev/null || echo "Bonjour Service registry key not found"

echo "Bonjour installation script completed."
