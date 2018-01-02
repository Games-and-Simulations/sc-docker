# TODOs:

- add support for C/C++ bots
- set custom game speed, see how we could integrate bwapi.ini?
- benchmark simulations on top game speed
- add option to launch starcraft game, and bots can connect to it repeatedly
  (save time for repeated plays)
- add some UUID for human games
- add support for singularity containers
- add cached parsed maps: https://github.com/vjurenka/BWMirror/tree/master/bwapi-data/BWTA2
- save replays after game is done into logs folder (or maybe some other one)
- output winner - X vs Y, if Y wins -> output "Y"
- viewing headful via VNC, simplify the process. Maybe use bwapi.ini for hosts?
- sound support (ALSA) :-)

This will go into another repo:

- support "tournament" mode, where a pool of bots can play against each other.
  Calculate ELO ratings.
- Distributed play - pool of workers which will receive info
  about who is to play with whom and they would run the simulation.
  Probably will use RabbitMQ.
