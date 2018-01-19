# Usage

## Help

    $ scbw.play -h

Contains a lot of options, quite well documented.

## Headful play

Launch headful play of [PurpleWave](https://sscaitournament.com/index.php?action=botDetails&bot=PurpleWave) and [CherryPi](https://sscaitournament.com/index.php?action=botDetails&bot=CherryPi) on default map.

    $ scbw.play --bots "PurpleWave" "CherryPi" --show_all

## Headless play

Simply add `--headless` option.

## Play against bot

    $ scbw.play --bots "PurpleWave" --human

Select a map, specify your race, and wait for bot(s) to join the game :)

You can put the RealVNC client to fullscreen and play comfortably.

(Although you might want to change your screen resolution to 800x600)

The GUI is going to be probably slower than normal game due to streaming via VNC.

### Play on the host

It is however possible to play the game on the host.

You will need two computers connected via a LAN network, one Windows (server, human player)
and one Linux (client, where the bot plays).

Create the game as a human player, and then run

    $ scbw.play --bots "PurpleWave" --opt "--net host"

This will bind the StarCraft ports to the host machine instead of virtual
network `sc_net`. (That's also why you need two computers).

This client was tested on linux only however, there might be
some problems on other OS (due to other OSes not having X server).

## Stop games that failed to finish

Stop all running games (docker containers):

    $  docker stop $(docker ps -a -q)

## Add your own bot

Simply place your java bot to `bots/` directory.

You can see logs from the games in `logs/` directory.

## Development

Build images locally:

    cd docker; ./build_images.sh

Use `--docker_image=starcraft:play` for testing.
