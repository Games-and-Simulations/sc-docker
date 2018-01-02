# Usage

## Headless play

Launch a headless play of [PurpleWave](https://github.com/dgant/PurpleWave) (P as Protoss) against Example Bot on default map.

    $ ./run_bots.sh ExampleBot:T PurpleWave:P
    f463e69d-7bbd-4638-a9a4

Let's watch logs to see what is happenning in headless mode.
You will need to have `tmux` installed.

    $ ./watch_logs.sh f46

(you don't need to specify the whole game name, just few chars)

After a moment, PurpleWave should win the game and you'll get similar output to this:

![Example log output](resources/example_log_output.png)

## Stop finished games

Stop all running games (docker containers):

    $  docker stop $(docker ps -a -q)

## Play against bot

Play against a bot (follow instructions)

    ./play_against_bots.sh PurpleWave:P

## Watch bot game

To watch headful game between bots (with gui):

    $ ./run_bots.sh ExampleBot:T PurpleWave:P
    $ tigervnc

Set `tigervnc` port to 5900, IP address `172.18.0.3` and password `starcraft`.

You have to join the game manually - via multiplayer.

IP address troubleshooting: you may need to find container IP address, try something like

    $ docker inspect -f '{{range .NetworkSss}}{{end}}' f73e612e-efb4-4b14-97e2_cfd8_bot_PurpleWave

Use proper container name.

## Help

    ./run_bots.sh --help
    ./play_against_bots.sh --help

## Add your own bot

Simply place your java bot to `bots/` directory.

You can see logs from the games in `logs/` directory.


## Development

Build images:

    ./build_images.sh

The `run_bots.sh` and `play_against_bots.sh` have special flags `--local`
which will lead to use of local instead of dockerhub images.
