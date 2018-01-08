# Basic images to build up X server with wine.
FROM ubuntu:xenial
MAINTAINER Michal Sustr <michal.sustr@aic.fel.cvut.cz>

ENV APP_DIR /app
ENV LOG_DIR $APP_DIR/logs

# Disable stupid install of mono/gecko, we don't need that
ENV WINEDLLOVERRIDES="mscoree,mshtml="

# Wine path
ENV WINEPREFIX /home/starcraft/.wine

# Make sure to run 32bit windows
ENV WINEARCH win32

# X display
ENV DISPLAY :0.0

# Make possible to use custom title bars
ENV WINEGUI_TITLEBAR "docker"

ENV STARCRAFT_UID 1000
ENV BASE_VNC_PORT 5900

# first create user and group for all the X Window stuff
# required to do this first so we have consistent uid/gid between server and client container
RUN set -x \
  && adduser \
    --uid $STARCRAFT_UID \
    --home /home/starcraft \
    --disabled-password \
    --shell /bin/bash \
    --ingroup users \
    --quiet \
    starcraft

# Install packages required for connecting against X Server
RUN set -x \
 && apt-get update -y \
 && apt-get install -y --no-install-recommends \
  xvfb xauth x11vnc x11-utils x11-xserver-utils

# Install packages for building the image
RUN set -x \
  && apt-get update -y \
  && apt-get install -y --no-install-recommends \
    curl unzip software-properties-common joe vim sudo wget curl screen tmux p7zip apt-transport-https winbind

# Install wine and related packages
RUN set -x \
    && curl -L https://dl.winehq.org/wine-builds/Release.key -o Release.key \
    && apt-key add Release.key \
    && apt-add-repository https://dl.winehq.org/wine-builds/ubuntu/ \
    && dpkg --add-architecture i386 \
    && apt-get update -y \
    && apt-get install -y --no-install-recommends \
        wine-staging-i386=2.20.0~xenial \
        wine-staging-amd64=2.20.0~xenial \
        wine-staging=2.20.0~xenial \
    && rm -rf /var/lib/apt/lists/* \
    && rm Release.key \
    && ln -s /opt/wine-staging/bin/wine /usr/bin/wine

ENV PATH $PATH:/opt/wine-staging/bin

# Use the latest version of winetricks
RUN curl -SL 'https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks' -o /usr/local/bin/winetricks \
    && chmod +x /usr/local/bin/winetricks

COPY scripts/winegui /usr/bin/winegui

RUN mkdir /app \
    && chown starcraft:users /app

RUN adduser starcraft sudo
RUN echo 'starcraft:starcraft' | chpasswd

# Wine really doesn't like to be run as root, so let's use a non-root user
WORKDIR $APP_DIR
USER starcraft
COPY entrypoints/wine_entrypoint.sh .

# Init wine.
# Let's run some command that will make sure the first init runs.
#
# windows doesn't have sleep, but this hack seems to work :-)
RUN set -eux && xvfb-run wine ping 127.0.0.1 -n 1 | cat

RUN mkdir -m 750 $LOG_DIR
VOLUME $LOG_DIR

EXPOSE $BASE_VNC_PORT

USER starcraft
CMD ["./wine_entrypoint.sh"]
