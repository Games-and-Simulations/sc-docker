### expected behaviour

### actual behaviour

### steps to reproduce

Please run the command issued with  `--log_level=DEBUG --log_verbose` parameters and log:

    scbw.play --bots krasi0 CherryPi --headless --log_level=DEBUG --log_verbose
    INFO checking docker version
    DEBUG Using docker API version b"'1.32'\n"
    INFO checking docker can run
    INFO checking docker has network sc_net
    DEBUG docker network id: b'0efb6d60a90a\n'
    INFO checking if there is local image starcraft:game
    DEBUG docker image id: b'26cc1b5de9df\n'
    DEBUG checking bot in /home/michal/.scbw/bots/krasi0
    DEBUG found bot in /home/michal/.scbw/bots/krasi0
    DEBUG checking bot in /home/michal/.scbw/bots/CherryPi
    DEBUG found bot in /home/michal/.scbw/bots/CherryPi
    DEBUG ['docker', 'run', '-d', '--rm', '--privileged', '--name', 'GAME_BED138A5_0_krasi0', '--volume', '/home/michal/.scbw/logs:/app/logs:rw', '--volume', '/home/michal/.scbw/bots:/app/bots:ro', '--volume', '/home/michal/.scbw/maps:/app/sc/maps:rw', '--volume', '/home/michal/.scbw/bwapi-data/BWTA:/app/sc/bwapi-data/BWTA:rw', '--volume', '/home/michal/.scbw/bwapi-data/BWTA2:/app/sc/bwapi-data/BWTA2:rw', '--net', 'sc_net', '--volume', '/home/michal/.scbw/bots/krasi0/write/GAME_BED138A5_0:/app/sc/bwapi-data/write:rw', '-e', 'PLAYER_NAME=krasi0', '-e', 'PLAYER_RACE=T', '-e', 'NTH_PLAYER=0', '-e', 'NUM_PLAYERS=2', '-e', 'GAME_NAME=GAME_BED138A5', '-e', 'MAP_NAME=/app/sc/maps/sscai/(2)Benzene.scx', '-e', 'GAME_TYPE=FREE_FOR_ALL', '-e', 'SPEED_OVERRIDE=0', '-e', 'BOT_NAME=krasi0', '-e', 'BOT_FILE=krasi0AIClient.exe', 'starcraft:game', '/app/play_bot.sh', '--game', 'GAME_BED138A5', '--name', 'krasi0', '--race', 'T', '--lan', '--host', '--map', '/app/sc/maps/sscai/(2)Benzene.scx']
    INFO launched BotPlayer:krasi0:T in container GAME_BED138A5_0_krasi0
    DEBUG ['docker', 'run', '-d', '--rm', '--privileged', '--name', 'GAME_BED138A5_1_CherryPi', '--volume', '/home/michal/.scbw/logs:/app/logs:rw', '--volume', '/home/michal/.scbw/bots:/app/bots:ro', '--volume', '/home/michal/.scbw/maps:/app/sc/maps:rw', '--volume', '/home/michal/.scbw/bwapi-data/BWTA:/app/sc/bwapi-data/BWTA:rw', '--volume', '/home/michal/.scbw/bwapi-data/BWTA2:/app/sc/bwapi-data/BWTA2:rw', '--net', 'sc_net', '--volume', '/home/michal/.scbw/bots/CherryPi/write/GAME_BED138A5_1:/app/sc/bwapi-data/write:rw', '-e', 'PLAYER_NAME=CherryPi', '-e', 'PLAYER_RACE=Z', '-e', 'NTH_PLAYER=1', '-e', 'NUM_PLAYERS=2', '-e', 'GAME_NAME=GAME_BED138A5', '-e', 'MAP_NAME=/app/sc/maps/sscai/(2)Benzene.scx', '-e', 'GAME_TYPE=FREE_FOR_ALL', '-e', 'SPEED_OVERRIDE=0', '-e', 'BOT_NAME=CherryPi', '-e', 'BOT_FILE=BWEnv.dll', 'starcraft:game', '/app/play_bot.sh', '--game', 'GAME_BED138A5', '--name', 'CherryPi', '--race', 'Z', '--lan', '--join']
    INFO launched BotPlayer:CherryPi:Z in container GAME_BED138A5_1_CherryPi
    INFO Checking if game has launched properly...
    DEBUG running containers: ['d09d26611377', 'd70fd9a17961']
    INFO Waiting until game is finished...
    DEBUG running containers: ['d09d26611377', 'd70fd9a17961']
    DEBUG running containers: ['d09d26611377', 'd70fd9a17961']
    ^CWARNING Caught interrupt, shutting down containers
    WARNING This can take a moment, please wait.
    DEBUG running containers: ['d09d26611377', 'd70fd9a17961']
    d09d26611377
    d70fd9a17961
    INFO Game cancelled.

### operating system

    win (version)
    mac (version)
    linux (version)

Ubuntu `lsb_release -a`:

    Distributor ID: Ubuntu
    Description:    Ubuntu 17.04
    Release:        17.04
    Codename:       zesty

### docker version

output of command `docker version`:

    Client:
     Version:      17.09.0-ce
     API version:  1.32
     Go version:   go1.8.3
     Git commit:   afdb6d4
     Built:        Tue Sep 26 22:42:45 2017
     OS/Arch:      linux/amd64

    Server:
     Version:      17.09.0-ce
     API version:  1.32 (minimum version 1.12)
     Go version:   go1.8.3
     Git commit:   afdb6d4
     Built:        Tue Sep 26 22:41:24 2017
     OS/Arch:      linux/amd64
     Experimental: false

### scbw version

output of command `scbw.play -v`

    0.2a16

