FROM starcraft:wine

ENV BOT_DIR /home/starcraft/.wine/drive_c/bot
ENV BOT_PATH $BOT_DIR/bot.dll
ENV BOT_DEBUG_PATH $BOT_DIR/bot_d.dll
ENV BWTA_DIR /home/starcraft/.wine/drive_c/bwta
ENV PATH $PATH:/opt/wine-staging/bin/:/home/starcraft
ENV SC_PATH="/home/starcraft/.wine/drive_c/Program Files/Starcraft"

# Get Starcraft game from ICCUP
RUN mkdir "${SC_PATH}" \
    && cd "${SC_PATH}" \
    && curl -SL 'http://files.theabyss.ru/sc/starcraft.zip' -o starcraft.zip \
    && unzip starcraft.zip -d . \
    && rm starcraft.zip \
    && chmod 755 -R .

# Get SSCAI maps pack
RUN cd "${SC_PATH}/maps" \
    && curl -SL 'http://sscaitournament.com/files/sscai_map_pack.zip' -o sscai_map_pack.zip \
    && unzip sscai_map_pack.zip -d . \
    && rm sscai_map_pack.zip \
    && chmod 755 -R .

# Get bwapi-data as of version 412
RUN curl -L https://github.com/lionax/bwapi/releases/download/v4.1.2/bwapi-data-4.1.2.zip -o /tmp/bwapi-data.zip \
   && unzip /tmp/bwapi-data.zip -d "${SC_PATH}" \
   && rm /tmp/bwapi-data.zip \
   && chmod 755 -R "${SC_PATH}/bwapi-data"

# Get BWTA 2.2
RUN curl -L https://bitbucket.org/auriarte/bwta2/downloads/BWTAlib_2.2.7z -o /tmp/bwta.7z \
    && 7zr x -o$BWTA_DIR /tmp/bwta.7z \
    && rm /tmp/bwta.7z \
    && mv $BWTA_DIR/BWTAlib_2.2/* $BWTA_DIR \
    && rm -R $BWTA_DIR/BWTAlib_2.2 \
    && chmod 755 -R $BWTA_DIR \
    && cp $BWTA_DIR/windows/libgmp-10.dll /home/starcraft/.wine/drive_c/windows \
    && cp $BWTA_DIR/windows/libmpfr-4.dll /home/starcraft/.wine/drive_c/windows

# Download bwheadless
RUN curl -L https://github.com/tscmoo/bwheadless/releases/download/v0.1/bwheadless.exe -o "$SC_PATH/bwheadless.exe"

# Just a useful link
RUN ln -s "/home/starcraft/.wine/drive_c/Program Files/Starcraft/" "/home/starcraft/.wine/drive_c/sc"

COPY launch_game.sh "/home/starcraft/launch_game.sh"

USER root
RUN chown -R starcraft:starcraft /home/starcraft

# Volume to place your bot inside
VOLUME $BOT_DIR
WORKDIR $BOT_DIR

# Run everything as starcraft user
# If you need to install something switch to root and then back to starcraft
USER starcraft
