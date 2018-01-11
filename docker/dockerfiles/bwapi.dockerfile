FROM starcraft:wine

ENV SC_DIR="$APP_DIR/sc"
ENV BWTA_DIR="$APP_DIR/bwta"
ENV BWAPI_DIR="$APP_DIR/bwapi"

ENV BOT_DIR="$APP_DIR/bots"
ENV MAP_DIR="$SC_DIR/maps"

ENV BWAPI_DATA_DIR="$SC_DIR/bwapi-data"
# BWAPI data dir is not shared with host, only its listed subdirs:
ENV BWAPI_DATA_BWTA_DIR="$BWAPI_DATA_DIR/BWTA"
ENV BWAPI_DATA_BWTA2_DIR="$BWAPI_DATA_DIR/BWTA2"
ENV BOT_DATA_READ_DIR="$BWAPI_DATA_DIR/read"
ENV BOT_DATA_WRITE_DIR="$BWAPI_DATA_DIR/write"
ENV BOT_DATA_AI_DIR="$BWAPI_DATA_DIR/AI"

ENV BOT_UID 1002

ENV PATH $PATH:/opt/wine-staging/bin/

USER root

# Get Starcraft game from ICCUP
RUN mkdir "${SC_DIR}" \
    && cd "${SC_DIR}" \
    && curl -SL 'http://files.theabyss.ru/sc/starcraft.zip' -o starcraft.zip \
    && unzip starcraft.zip -d . \
    && rm starcraft.zip \
    && rm -rf $SC_DIR/characters/*

# Get BWTA 2.2
RUN curl -L https://bitbucket.org/auriarte/bwta2/downloads/BWTAlib_2.2.7z -o /tmp/bwta.7z \
    && 7zr x -o$BWTA_DIR /tmp/bwta.7z \
    && rm /tmp/bwta.7z \
    && mv $BWTA_DIR/BWTAlib_2.2/* $BWTA_DIR \
    && rm -R $BWTA_DIR/BWTAlib_2.2 \
    && cp $BWTA_DIR/windows/libgmp-10.dll $WINEPREFIX/drive_c/windows \
    && cp $BWTA_DIR/windows/libmpfr-4.dll $WINEPREFIX/drive_c/windows

# Download bwheadless
RUN curl -L https://github.com/tscmoo/bwheadless/releases/download/v0.1/bwheadless.exe -o "$SC_DIR/bwheadless.exe"

# Create bot user which will have access only to BOT_DATA_*_DIR
RUN set -x \
    && addgroup bot \
    && adduser \
    --uid $BOT_UID \
    --ingroup bot \
    --home /home/bot \
    --disabled-password \
    --shell /bin/bash \
    --quiet \
    bot

RUN rm -rf $MAP_DIR $BOT_DIR

# copy relevant BWAPI versions (cached)
COPY bwapi $BWAPI_DIR
COPY scripts/launch_game /usr/bin/launch_game
COPY default* $SC_DIR/characters/

RUN chown -R starcraft:users $APP_DIR
RUN chmod -R 750 $APP_DIR
RUN chmod -R 750 $WINEPREFIX
RUN chmod -R 770 $SC_DIR
RUN cp -r /home/starcraft/.wine /home/bot/.wine \
    && chown -R bot:users /home/bot/.wine

# these are ports that SC uses,
# according to http://wiki.teamliquid.net/starcraft/Port_Forwarding
EXPOSE 6111:6119 6111:6119/udp

# Run starcraft as starcraft user, and bot as bot user :)
#
# If you need to install something switch to root and then back to starcraft,
# but you shouldn't usually need root. Wine requires running everything as non-root user!

# todo: permissions -AI ro, read/save rw
RUN mkdir -m 775 $BWAPI_DATA_DIR $BWAPI_DATA_BWTA_DIR $BWAPI_DATA_BWTA2_DIR
RUN mkdir -m 755 $MAP_DIR $BOT_DIR $BOT_DATA_AI_DIR
VOLUME $BWAPI_DATA_BWTA_DIR $BWAPI_DATA_BWTA2_DIR $MAP_DIR $BOT_DIR

RUN mkdir -m 775 $BOT_DATA_READ_DIR
RUN mkdir -m 775 $BOT_DATA_WRITE_DIR
VOLUME $BOT_DATA_READ_DIR $BOT_DATA_WRITE_DIR

RUN chown starcraft:users -R \
    $BWAPI_DATA_DIR $BWAPI_DATA_BWTA_DIR $BWAPI_DATA_BWTA2_DIR $MAP_DIR $BOT_DATA_AI_DIR $BOT_DIR $BOT_DATA_READ_DIR $BOT_DATA_WRITE_DIR

USER starcraft

RUN echo "umask 0027" >> /home/starcraft/.bashrc

WORKDIR $APP_DIR
CMD ["./bwapi_entrypoint.sh"]
