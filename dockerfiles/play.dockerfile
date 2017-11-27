FROM starcraft:java

USER starcraft

WORKDIR $HOME_DIR

COPY entrypoints/play_entrypoint.sh .

# these are ports that SC uses, according to http://wiki.teamliquid.net/starcraft/Port_Forwarding
EXPOSE 6111 6112 6113 6114 6115 6116 6117 6118 6119

CMD ["./play_entrypoint.sh"]
