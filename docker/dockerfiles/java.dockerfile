FROM starcraft:play
MAINTAINER Michal Sustr <michal.sustr@aic.fel.cvut.cz>


ENV JAVA_DIR="$APP_DIR/java"

#####################################################################
USER starcraft
WORKDIR $APP_DIR

COPY --chown=starcraft:users jre_8_32bit_noinstall.zip jre.zip
RUN set -x \
    && unzip -q jre.zip \
    && mv jre1.8.0_152/ $JAVA_DIR/ \
    && rm jre.zip

COPY scripts/win_java32 /usr/bin/win_java32
