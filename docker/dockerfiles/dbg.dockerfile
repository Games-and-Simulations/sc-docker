FROM starcraft:game

# Switch to root for package installation
USER root

# Install X11 components, VNC server, debugging and LAN networking tools
RUN set -x \
 && apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt install -y --no-install-recommends \
    xauth \
    kde-cli-tools \
    procps \
    psmisc \
    htop \
    nano \
    vim \
    wget \
    curl \
    net-tools \
    xvfb \
    x11vnc \
    strace \
    tcpdump \
    tshark \
    wireshark-common \
    netstat-nat \
    lsof \
    gdb \
    ltrace \
    cabextract \
    socat \
    ncat \
    iptables \
    iproute2 \
    iputils-ping \
    dnsutils \
    bridge-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy debugging scripts from debug subdirectory
COPY --chown=starcraft:users scripts/debug/DEBUG_network_debug.sh /app/scripts/DEBUG_network_debug.sh
COPY --chown=starcraft:users scripts/debug/DEBUG_network_analysis.sh /app/scripts/DEBUG_network_analysis.sh
COPY --chown=starcraft:users scripts/debug/DEBUG_auto_startup.sh /app/scripts/DEBUG_auto_startup.sh
COPY --chown=starcraft:users scripts/debug/DEBUG_udp_receiver.sh /app/scripts/DEBUG_udp_receiver.sh
COPY --chown=starcraft:users scripts/debug/DEBUG_udp_sender.sh /app/scripts/DEBUG_udp_sender.sh
COPY --chown=starcraft:users scripts/debug/DEBUG_udp_relay.sh /app/scripts/DEBUG_udp_relay.sh
# These patch scripts may not exist in all forks; copy if present
COPY --chown=starcraft:users scripts/debug/DEBUG_patch_play_common.sh /app/scripts/DEBUG_patch_play_common.sh
COPY --chown=starcraft:users scripts/debug/DEBUG_patch_gui.sh /app/scripts/DEBUG_patch_gui.sh

# Make scripts executable (ignore if missing)
RUN chmod +x /app/scripts/DEBUG_network_debug.sh \
    && chmod +x /app/scripts/DEBUG_network_analysis.sh \
    && chmod +x /app/scripts/DEBUG_auto_startup.sh \
    && chmod +x /app/scripts/DEBUG_udp_receiver.sh \
    && chmod +x /app/scripts/DEBUG_udp_sender.sh \
    && chmod +x /app/scripts/DEBUG_udp_relay.sh \
    || true
RUN chmod +x /app/scripts/DEBUG_patch_play_common.sh /app/scripts/DEBUG_patch_gui.sh || true

# Add UDP LAN relay script used for LAN discovery and broadcast forwarding
RUN echo '#!/bin/bash' > /app/scripts/udp_lan_relay.sh \
    && echo '# UDP LAN Relay for StarCraft' >> /app/scripts/udp_lan_relay.sh \
    && echo 'echo "Starting UDP LAN relay for StarCraft..."' >> /app/scripts/udp_lan_relay.sh \
    && echo '' >> /app/scripts/udp_lan_relay.sh \
    && echo '# Get container network info' >> /app/scripts/udp_lan_relay.sh \
    && echo 'MY_IP=$(hostname -I | cut -d" " -f1)' >> /app/scripts/udp_lan_relay.sh \
    && echo 'echo "My IP: $MY_IP"' >> /app/scripts/udp_lan_relay.sh \
    && echo '' >> /app/scripts/udp_lan_relay.sh \
    && echo '# Function to relay UDP broadcasts' >> /app/scripts/udp_lan_relay.sh \
    && echo 'relay_port() {' >> /app/scripts/udp_lan_relay.sh \
    && echo '    local PORT=$1' >> /app/scripts/udp_lan_relay.sh \
    && echo '    echo "Relaying UDP port $PORT..."' >> /app/scripts/udp_lan_relay.sh \
    && echo '    # Listen for broadcasts and forward them' >> /app/scripts/udp_lan_relay.sh \
    && echo '    socat -u UDP4-RECVFROM:$PORT,broadcast,reuseaddr,fork UDP4-DATAGRAM:255.255.255.255:$PORT,broadcast &' >> /app/scripts/udp_lan_relay.sh \
    && echo '    # Also listen and forward to subnet broadcast' >> /app/scripts/udp_lan_relay.sh \
    && echo '    SUBNET=$(echo $MY_IP | cut -d. -f1-3)' >> /app/scripts/udp_lan_relay.sh \
    && echo '    socat -u UDP4-RECVFROM:$PORT,reuseaddr,fork UDP4-DATAGRAM:$SUBNET.255:$PORT,broadcast &' >> /app/scripts/udp_lan_relay.sh \
    && echo '}' >> /app/scripts/udp_lan_relay.sh \
    && echo '' >> /app/scripts/udp_lan_relay.sh \
    && echo '# Start relays for StarCraft ports' >> /app/scripts/udp_lan_relay.sh \
    && echo 'relay_port 6111  # Discovery port' >> /app/scripts/udp_lan_relay.sh \
    && echo 'relay_port 6112  # Game data port' >> /app/scripts/udp_lan_relay.sh \
    && echo '' >> /app/scripts/udp_lan_relay.sh \
    && echo 'echo "UDP relay running. StarCraft LAN discovery should work now."' >> /app/scripts/udp_lan_relay.sh \
    && chmod +x /app/scripts/udp_lan_relay.sh

# Switch to starcraft user
USER starcraft
# Keep the working directory as /app (inherited from starcraft:game)
WORKDIR /app

# Note: Debug scripts are available but not automatically integrated
# Users can manually run debugging tools as needed
# See DEBUG.md for usage instructions

# Ensure Wine prefix exists and install key networking components via winetricks
# Use xvfb-run to avoid any display dependency at build time
RUN winetricks -q --force cmd || true \
 && xvfb-run -a winetricks -q directplay wininet winhttp urlmon || true

# Set up Wine environment variables for VNC
ENV DISPLAY=:0
ENV WINEARCH=win32
ENV WINEPREFIX=/home/starcraft/.wine

# Expose VNC port
EXPOSE 5900

# Create a VNC desktop startup script (available but not used by default)
# Users can manually run: /home/starcraft/start_vnc_desktop.sh for GUI debugging
RUN echo '#!/bin/bash' > /home/starcraft/start_vnc_desktop.sh \
    && echo 'echo "Starting Xvfb virtual display..."' >> /home/starcraft/start_vnc_desktop.sh \
    && echo 'Xvfb :0 -screen 0 1280x720x24 > /tmp/xvfb.log 2>&1 &' >> /home/starcraft/start_vnc_desktop.sh \
    && echo 'sleep 2' >> /home/starcraft/start_vnc_desktop.sh \
    && echo 'echo "Starting VNC server on :0 (port 5900)..."' >> /home/starcraft/start_vnc_desktop.sh \
    && echo 'x11vnc -forever -nopw -display :0 > /tmp/vnc.log 2>&1 &' >> /home/starcraft/start_vnc_desktop.sh \
    && echo 'sleep 2' >> /home/starcraft/start_vnc_desktop.sh \
    && echo 'echo "Starting Wine desktop environment..."' >> /home/starcraft/start_vnc_desktop.sh \
    && echo 'echo "VNC server running on port 5900"' >> /home/starcraft/start_vnc_desktop.sh \
    && echo 'echo "Connect with: vncviewer localhost:5900"' >> /home/starcraft/start_vnc_desktop.sh \
    && echo 'wine explorer /desktop=debug,1280x720' >> /home/starcraft/start_vnc_desktop.sh \
    && chmod +x /home/starcraft/start_vnc_desktop.sh

# Remove Xvfb -auth from the runtime script inside debug image to simplify headless display
RUN sed -i 's/ -auth ~\/.Xauthority//g' /app/play_common.sh || true

# No custom CMD - inherit default behavior from parent image (starcraft:game)
# Debug container now starts exactly like game container
# Users can access debugging tools manually or through scbw.play
