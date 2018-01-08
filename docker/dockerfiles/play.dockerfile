FROM starcraft:java

USER root
WORKDIR $APP_DIR

COPY entrypoints/play_* ./
RUN chown starcraft:users play_* && chmod 750 play_*

USER starcraft
CMD ["/app/play_entrypoint.sh"]
