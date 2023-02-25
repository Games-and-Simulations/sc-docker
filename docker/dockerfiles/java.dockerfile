FROM starcraft:play
LABEL maintainer="Michal Sustr <michal.sustr@aic.fel.cvut.cz>"


ENV JAVA_DIR="$APP_DIR/java"

#####################################################################
USER starcraft
WORKDIR $APP_DIR

RUN set -x \
    && wget https://corretto.aws/downloads/latest/amazon-corretto-8-x86-windows-jre.zip -O jre.zip \
    && unzip jre.zip\
    && mv jre*/ $JAVA_DIR/ \
    && rm jre.zip

COPY scripts/win_java32 /usr/bin/win_java32
