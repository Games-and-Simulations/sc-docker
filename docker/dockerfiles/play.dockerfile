FROM starcraft:java

USER root
WORKDIR $APP_DIR

COPY entrypoints/play_* ./
COPY entrypoints/hook_* ./
RUN chown starcraft:users play_* && chmod 750 play_* \
    && chown starcraft:users hook_* && chmod 750 hook_*
COPY protocols /etc/protocols
COPY requirements $APP_DIR/requirements
COPY dlls $SC_DIR/

USER starcraft
CMD ["/app/play_entrypoint.sh"]
