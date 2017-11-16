# Basic images to build up X server with wine.
FROM ubuntu:xenial
MAINTAINER Michal Sustr <michal.sustr+sc@gmail.com>

# Define which versions we need
ENV WINE_MONO_VERSION 4.5.6
ENV WINE_GECKO_VERSION 2.47

# Make sure to run 32bit windows
ENV WINEPREFIX /home/starcraft/.wine
ENV WINEARCH win32

# X display
ENV DISPLAY :0.0

# first create user and group for all the X Window stuff
# required to do this first so we have consistent uid/gid between server and client container
RUN set -x \
  && addgroup --system starcraft \
  && adduser \
    --home /home/starcraft \
    --disabled-password \
    --shell /bin/bash \
    --gecos "user for running an torcraft application" \
    --ingroup starcraft \
    --quiet \
    starcraft

# Install packages required for connecting against X Server
RUN set -x \
 && apt-get update \
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
RUN set -x \
    && curl -L https://dl.winehq.org/wine-builds/Release.key -o Release.key \
    && apt-key add Release.key \
    && apt-add-repository https://dl.winehq.org/wine-builds/ubuntu/ \
    && dpkg --add-architecture i386 \
    && apt-get update -y \
    && apt-get install -y --no-install-recommends \
        winehq-staging=2.20.0~xenial \
    && rm -rf /var/lib/apt/lists/* \
    && rm Release.key


# Use the latest version of winetricks
RUN curl -SL 'https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks' -o /usr/local/bin/winetricks \
    && chmod +x /usr/local/bin/winetricks

# Wine really doesn't like to be run as root, so let's use a non-root user
RUN adduser starcraft sudo
RUN echo 'starcraft:starcraft' | chpasswd

# Disable stupid install of mono/gecko, we don't need that
ENV WINEDLLOVERRIDES="mscoree,mshtml="

COPY entrypoint.sh /entrypoint.sh

WORKDIR /home/starcraft
USER starcraft

# Set some basic wine / vnc settings
RUN echo "alias winegui='wine explorer /desktop=DockerDesktop,1024x768'" > /home/starcraft/.bash_aliases
# Init wine.
# Let's run some command that will make sure the first init runs.
#
# windows doesn't have sleep, but this hack seems to work :-)
RUN set -eux && xvfb-run wine ping 127.0.0.1 -n 1 | cat


ENTRYPOINT ["/entrypoint.sh"]
