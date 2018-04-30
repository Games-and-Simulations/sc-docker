FROM starcraft:wine
LABEL maintainer="Michal Sustr <michal.sustr@aic.fel.cvut.cz>"

ENV SC_DIR="$APP_DIR/sc"
ENV BWTA_DIR="$APP_DIR/bwta"
ENV BWAPI_DIR="$APP_DIR/bwapi"
ENV TM_DIR="$APP_DIR/tm"
ENV BOT_DIR="$APP_DIR/bot"
ENV MAP_DIR="$SC_DIR/maps"
ENV ERRORS_DIR="$SC_DIR/Errors"
ENV BWAPI_DATA_DIR="$SC_DIR/bwapi-data"

ENV BOT_DATA_AI_DIR="$BWAPI_DATA_DIR/AI"
ENV BOT_DATA_READ_DIR="$BWAPI_DATA_DIR/read"

# Entire BWAPI data dir is not shared with host, only these subdirs:
ENV BWAPI_DATA_BWTA_DIR="$BWAPI_DATA_DIR/BWTA"
ENV BWAPI_DATA_BWTA2_DIR="$BWAPI_DATA_DIR/BWTA2"
ENV BOT_DATA_WRITE_DIR="$BWAPI_DATA_DIR/write"

ENV BOT_UID 1001

# these are ports that SC uses,
# according to http://wiki.teamliquid.net/starcraft/Port_Forwarding
EXPOSE 6111:6119 6111:6119/udp

#####################################################################
USER root

# Create bot user which will have access only to BOT_DATA_*_DIR
RUN set -x \
    && addgroup bot \
    && adduser \
    --uid $BOT_UID \
    --ingroup users \
    --home /home/bot \
    --disabled-password \
    --shell /bin/bash \
    --quiet \
    bot \
    && usermod -aG bot bot

# Sometime there was a weird error with protocols
COPY protocols /etc/protocols

#####################################################################
USER starcraft
WORKDIR $APP_DIR

# Create SC dir
RUN mkdir "${SC_DIR}"

# Copy dll files
COPY --chown=starcraft:users dlls/* $WINEPREFIX/drive_c/windows/system32/

# Install more dlls from winetricks. It requires X-server so let's run in bg for now :)
RUN /bin/bash -c "Xvfb :0 -auth ~/.Xauthority -screen 0 640x480x24 & winetricks -q vcrun2015"

# Download bwheadless
RUN curl -L https://github.com/tscmoo/bwheadless/releases/download/v0.1/bwheadless.exe \
    -o "$SC_DIR/bwheadless.exe"

# Copy relevant BWAPI versions (cached)
COPY --chown=starcraft:users bwapi $BWAPI_DIR
COPY --chown=starcraft:users tm $TM_DIR

COPY scripts/launch_game /usr/bin/launch_game

#####################################################################
# Create wine profile for bot
USER root
RUN cp -r /home/starcraft/.wine /home/bot/.wine \
    && chown -R bot:users /home/bot/.wine

#####################################################################
USER starcraft
CMD ["./bwapi_entrypoint.sh"]
