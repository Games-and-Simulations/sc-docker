# Usage

## Help

    $ python sc.py -h

Contains a lot of options.

## Headless play

Launch headful play of [PurpleWave](https://sscaitournament.com/index.php?action=botDetails&bot=PurpleWave) and [CherryPi](https://sscaitournament.com/index.php?action=botDetails&bot=CherryPi) on default map.

    $ python sc.py --bots "PurpleWave" "CherryPi" --show_all

## Play against bot

Play against a bot

    $ python sc.py --bots "PurpleWave" --human

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
