FROM starcraft:java
LABEL maintainer="Michal Sustr <michal.sustr@aic.fel.cvut.cz>"

#####################################################################
USER starcraft
WORKDIR $SC_DIR

# Get Starcraft game from ICCUP
COPY starcraft.zip /tmp/starcraft.zip
COPY player* /tmp/

RUN unzip -q /tmp/starcraft.zip -d /tmp/starcraft \
    && rm -rf /tmp/starcraft/characters/* /tmp/starcraft/maps/* \
    && chown starcraft:users -R /tmp/starcraft \
    && cp /tmp/player* /tmp/starcraft/characters \
    && chown starcraft:users -R /tmp/starcraft/characters

USER root
RUN rm /tmp/starcraft.zip \
    && mv /tmp/starcraft/* $SC_DIR/

USER starcraft

RUN mkdir -m 775 $BWAPI_DATA_DIR $BWAPI_DATA_BWTA_DIR $BWAPI_DATA_BWTA2_DIR
RUN mkdir -m 755 $BOT_DIR $BOT_DATA_AI_DIR $BOT_DATA_READ_DIR
RUN mkdir -m 777 $BOT_DATA_WRITE_DIR $ERRORS_DIR
VOLUME $BWAPI_DATA_BWTA_DIR $BWAPI_DATA_BWTA2_DIR $MAP_DIR $BOT_DIR $BOT_DATA_WRITE_DIR $ERRORS_DIR

RUN echo "umask 0027" >> /home/starcraft/.bashrc

WORKDIR $APP_DIR
