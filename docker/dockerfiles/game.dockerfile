FROM starcraft:java
MAINTAINER Michal Sustr <michal.sustr@aic.fel.cvut.cz>

#####################################################################
USER starcraft
WORKDIR $SC_DIR

# Get Starcraft game from ICCUP
COPY --chown=starcraft:users starcraft.zip $SC_DIR
RUN cd "${SC_DIR}" \
    && unzip starcraft.zip -d . \
    && rm starcraft.zip \
    && rm -rf $SC_DIR/characters/* $MAP_DIR/*

# Copy default characters
COPY --chown=starcraft:users default* $SC_DIR/characters/

RUN mkdir -m 775 $BWAPI_DATA_DIR $BWAPI_DATA_BWTA_DIR $BWAPI_DATA_BWTA2_DIR
RUN mkdir -m 755 $BOT_DIR $BOT_DATA_AI_DIR $BOT_DATA_READ_DIR
RUN mkdir -m 777 $BOT_DATA_WRITE_DIR
VOLUME $BWAPI_DATA_BWTA_DIR $BWAPI_DATA_BWTA2_DIR $MAP_DIR $BOT_DIR $BOT_DATA_WRITE_DIR

RUN echo "umask 0027" >> /home/starcraft/.bashrc

WORKDIR $APP_DIR
