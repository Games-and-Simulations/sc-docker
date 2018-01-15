# TODOs:

- Add tournament dll to save frame times & scores
- Play against in-game AI
- Play on multiple computers
- Launch game, and bots can connect to it repeatedly (save time for repeated plays)
- Support for singularity containers
- Add cached parsed maps: https://github.com/vjurenka/BWMirror/tree/master/bwapi-data/BWTA2
- Sound support (ALSA) for human player
- Copy crash files from SC folder outside (java crashes are in Z:\app\sc\hs_err_pid8.log)
- Try to make the docker image smaller

This will go into another repo:

- support "tournament" mode, where a pool of bots can play against each other.
  Calculate ELO ratings.
- Distributed play - pool of workers which will receive info
  about who is to play with whom and they would run the simulation.
  Probably will use RabbitMQ.
