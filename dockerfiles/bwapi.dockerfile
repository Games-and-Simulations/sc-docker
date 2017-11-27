FROM starcraft:wine

ENV BOT_DIR $HOME_DIR/.wine/drive_c/bot
ENV BWTA_DIR $HOME_DIR/.wine/drive_c/bwta
ENV SC_DIR="${HOME_DIR}/.wine/drive_c/Program Files/Starcraft"

ENV PATH $PATH:/opt/wine-staging/bin/:$HOME_DIR

USER root

# Get Starcraft game from ICCUP
RUN mkdir "${SC_DIR}" \
    && cd "${SC_DIR}" \
    && curl -SL 'http://files.theabyss.ru/sc/starcraft.zip' -o starcraft.zip \
    && unzip starcraft.zip -d . \
    && rm starcraft.zip \
    && chmod 755 -R .

# Get SSCAI maps pack
RUN cd "${SC_DIR}/maps" \
    && curl -SL 'http://sscaitournament.com/files/sscai_map_pack.zip' -o sscai_map_pack.zip \
    && unzip sscai_map_pack.zip -d . \
    && rm sscai_map_pack.zip \
    && chmod 755 -R .

# Get bwapi-data as of version 412
RUN curl -L https://github.com/lionax/bwapi/releases/download/v4.1.2/bwapi-data-4.1.2.zip -o /tmp/bwapi-data.zip \
   && unzip /tmp/bwapi-data.zip -d "${SC_DIR}" \
   && rm /tmp/bwapi-data.zip \
   && chmod 755 -R "${SC_DIR}/bwapi-data"

# Get BWTA 2.2
RUN curl -L https://bitbucket.org/auriarte/bwta2/downloads/BWTAlib_2.2.7z -o /tmp/bwta.7z \
    && 7zr x -o$BWTA_DIR /tmp/bwta.7z \
    && rm /tmp/bwta.7z \
    && mv $BWTA_DIR/BWTAlib_2.2/* $BWTA_DIR \
    && rm -R $BWTA_DIR/BWTAlib_2.2 \
    && chmod 755 -R $BWTA_DIR \
    && cp $BWTA_DIR/windows/libgmp-10.dll $HOME_DIR/.wine/drive_c/windows \
    && cp $BWTA_DIR/windows/libmpfr-4.dll $HOME_DIR/.wine/drive_c/windows

# Download bwheadless
RUN curl -L https://github.com/tscmoo/bwheadless/releases/download/v0.1/bwheadless.exe -o "$SC_DIR/bwheadless.exe"

# Just a useful link
RUN ln -s "${HOME_DIR}/.wine/drive_c/Program Files/Starcraft/" "${HOME_DIR}/.wine/drive_c/sc"

COPY scripts/* $HOME_DIR

RUN chown -R starcraft:starcraft $HOME_DIR
RUN apt update && apt install -y screen

# Volume to place your bot inside
VOLUME $BOT_DIR
# Volume where logs will be stored
VOLUME $LOG_DIR

# Run everything as starcraft user.
#
# If you need to install something switch to root and then back to starcraft,
# but you shouldn't usually need root. Wine requires running everything as non-root user!
USER starcraft

WORKDIR $HOME_DIR
COPY entrypoints/bwapi_entrypoint.sh .

CMD ["./bwapi_entrypoint.sh"]
