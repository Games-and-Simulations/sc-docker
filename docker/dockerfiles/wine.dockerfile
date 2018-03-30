# Basic images to build up X server with wine.
FROM ubuntu:xenial
LABEL maintainer="Michal Sustr <michal.sustr@aic.fel.cvut.cz>"

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

EXPOSE $BASE_VNC_PORT

#####################################################################
USER root

# First create starcraft user and users group
# for all the X Window stuff.
#
# Required to do this first so we have consistent
# uid/gid between server and client container.
#
# Add this user to sudo group for later use if needed.
RUN set -x \
  && adduser \
    --uid $STARCRAFT_UID \
    --home /home/starcraft \
    --disabled-password \
    --shell /bin/bash \
    --ingroup users \
    --quiet \
    starcraft \
  && adduser starcraft sudo \
  && echo 'starcraft:starcraft' | chpasswd


# Install packages required for connecting against X Server
# and for building the image, and some other helpful tools.
#
# Install wine and related packages.
#
# Use the latest version of winetricks
RUN set -x \
  && apt-get update -y \
  && apt-get install -y --no-install-recommends \
    xvfb xauth x11vnc x11-utils x11-xserver-utils xdotool \
    curl unzip software-properties-common joe vim sudo wget curl tree screen tmux p7zip apt-transport-https winbind \
    binutils cabextract unrar zenity \
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
  && ln -s /opt/wine-staging/bin/wine /usr/bin/wine \
  && curl -SL 'https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks' \
        -o /usr/local/bin/winetricks \
  && chmod +x /usr/local/bin/winetricks

ENV PATH $PATH:/opt/wine-staging/bin/

COPY scripts/winegui /usr/bin/winegui

# Create root APP_DIR
RUN mkdir $APP_DIR && chown starcraft:users $APP_DIR
WORKDIR $APP_DIR

#####################################################################
# Wine shouldn't be run as root, so let's use a 'starcraft' user
USER starcraft

RUN mkdir -m 700 $LOG_DIR
VOLUME $LOG_DIR

# Init wine.
# Let's run some command that will make sure the first init runs.
#
# windows doesn't have sleep, but this hack seems to work :-)
RUN set -eux && xvfb-run wine ping 127.0.0.1 -n 1 | cat

