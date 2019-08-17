FROM starcraft:play
LABEL maintainer="Michal Sustr <michal.sustr@aic.fel.cvut.cz>"


ENV JAVA_DIR="$APP_DIR/java"

#####################################################################
USER starcraft
WORKDIR $APP_DIR

ADD --chown=starcraft:users https://d2znqt9b1bc64u.cloudfront.net/amazon-corretto-8.202.08.2-windows-x86-jre.zip jre.zip
RUN set -x \
    && unzip jre.zip\
    && mv jre1.8.0_202/ $JAVA_DIR/ \
    && rm jre.zip

COPY scripts/win_java32 /usr/bin/win_java32