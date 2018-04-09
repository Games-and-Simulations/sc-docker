FROM starcraft:play
LABEL maintainer="Michal Sustr <michal.sustr@aic.fel.cvut.cz>"


ENV JAVA_DIR="$APP_DIR/java"

#####################################################################
USER starcraft
WORKDIR $APP_DIR

COPY --chown=starcraft:users jre-8u161-windows-i586.tar.gz jre.tar.gz
RUN set -x \
    && tar -xzf jre.tar.gz \
    && mv jre1.8.0_161/ $JAVA_DIR/ \
    && rm jre.tar.gz

COPY scripts/win_java32 /usr/bin/win_java32
