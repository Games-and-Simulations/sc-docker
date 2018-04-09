FROM starcraft:bwapi
LABEL maintainer="Michal Sustr <michal.sustr@aic.fel.cvut.cz>"

USER starcraft
WORKDIR $APP_DIR

COPY --chown=starcraft:users scripts/play_* ./
COPY --chown=starcraft:users scripts/hook_* ./

CMD ["/app/play_entrypoint.sh"]
