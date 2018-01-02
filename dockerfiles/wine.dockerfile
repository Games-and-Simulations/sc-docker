# Basic images to build up X server with wine.
FROM ubuntu:xenial
MAINTAINER Michal Sustr <michal.sustr+sc@gmail.com>

ENV HOME_DIR /home/starcraft
ENV LOG_DIR $HOME_DIR/logs

# Define which versions we need
ENV WINE_MONO_VERSION 4.5.6
ENV WINE_GECKO_VERSION 2.47

# Make sure to run 32bit windows
ENV WINEPREFIX $HOME_DIR/.wine
ENV WINEARCH win32

# X display
ENV DISPLAY :0.0

# first create user and group for all the X Window stuff
# required to do this first so we have consistent uid/gid between server and client container
RUN set -x \
  && addgroup --system starcraft \
  && adduser \
    --home $HOME_DIR \
    --disabled-password \
    --shell /bin/bash \
    --ingroup starcraft \
    --quiet \
    starcraft

# Install packages required for connecting against X Server
RUN set -x \
 && apt-get update -y \
 && apt-get install -y --no-install-recommends \
  xvfb \
  xauth \
  x11vnc \
  x11-utils \
  x11-xserver-utils

# Install packages for building the image
RUN set -x \
  && apt-get update -y \
  && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    software-properties-common \
    joe \
    vim \
    sudo \
    curl \
    p7zip \
    apt-transport-https \
    winbind

# This is deprecated, but using official source according to
# https://launchpad.net/~ubuntu-wine/+archive/ubuntu/ppa
# does not contain newer wine builds :facepalm:
#RUN add-apt-repository ppa:ubuntu-wine/ppa -y


# Install wine and related packages
# todo: wine-devel=2.21.0~xenial is not a proper version fixation - it might be removed with new version?
#       but no idea how it should be fixated... hopefully newer versions will not break the whole build
#
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
    && rm Release.key

ENV PATH $PATH:/opt/wine-staging/bin

# Use the latest version of winetricks
RUN curl -SL 'https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks' -o /usr/local/bin/winetricks \
    && chmod +x /usr/local/bin/winetricks

# Wine really doesn't like to be run as root, so let's use a non-root user
RUN adduser starcraft sudo
RUN echo 'starcraft:starcraft' | chpasswd

# Disable stupid install of mono/gecko, we don't need that
ENV WINEDLLOVERRIDES="mscoree,mshtml="

WORKDIR $HOME_DIR
USER starcraft

RUN mkdir $LOG_DIR

COPY entrypoints/wine_entrypoint.sh .

# Set some basic wine / vnc settings
COPY scripts/winegui /usr/bin/winegui

# Init wine.
# Let's run some command that will make sure the first init runs.
#
# windows doesn't have sleep, but this hack seems to work :-)
RUN set -eux && xvfb-run wine ping 127.0.0.1 -n 1 | cat


CMD ["./wine_entrypoint.sh"]
