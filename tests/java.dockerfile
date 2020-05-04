FROM starcraft:play
LABEL maintainer="Michal Sustr <michal.sustr@aic.fel.cvut.cz>"


ENV JAVA_DIR="$APP_DIR/java"

#####################################################################
USER starcraft
WORKDIR $APP_DIR

ADD --chown=starcraft:users https://github.com/AdoptOpenJDK/openjdk8-binaries/releases/download/jdk8u252-b09.1/OpenJDK8U-jre_x86-32_windows_hotspot_8u252b09.zip jre.zip
RUN set -x \
    && unzip jre.zip\
    && mv jdk8u252-b09-jre/ $JAVA_DIR/ \
    && rm jre.zip

COPY scripts/win_java32 /usr/bin/win_java32
