FROM starcraft:bwapi

USER starcraft

WORKDIR $HOME_DIR

COPY resources/jre_8_32bit_noinstall.zip jre.zip
RUN set -x \
    && unzip jre.zip \
    && mv jre1.8.0_152/ java/ \
    && rm jre.zip


