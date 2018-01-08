FROM starcraft:java

USER root
WORKDIR $APP_DIR

COPY entrypoints/play_* ./
COPY entrypoints/hook_* ./
RUN chown starcraft:users play_* && chmod 750 play_* \
    && chown starcraft:users hook_* && chmod 750 hook_*

USER starcraft
CMD ["/app/play_entrypoint.sh"]
