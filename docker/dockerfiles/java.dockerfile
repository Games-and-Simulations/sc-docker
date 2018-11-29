FROM starcraft:play
LABEL maintainer="Michal Sustr <michal.sustr@aic.fel.cvut.cz>"


ENV JAVA_DIR="$APP_DIR/java"

#####################################################################
USER starcraft
WORKDIR $APP_DIR

COPY --chown=starcraft:users java-1.8.0-openjdk-1.8.0.191-1.b12.ojdkbuild.windows.x86.zip jdk.zip
RUN set -x \
    && unzip jdk.zip\
    && mv java-1.8.0-openjdk-1.8.0.191-1.b12.ojdkbuild.windows.x86/ $JAVA_DIR/ \
    && rm jdk.zip

COPY scripts/win_java32 /usr/bin/win_java32
