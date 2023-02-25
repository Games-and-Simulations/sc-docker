# Usage

## Help

    $ scbw.play -h

Contains a lot of options, quite well documented.

## Headful play

Launch headful play of [PurpleWave](https://sscaitournament.com/index.php?action=botDetails&bot=PurpleWave) and [CherryPi](https://sscaitournament.com/index.php?action=botDetails&bot=CherryPi) on default map.

    $ scbw.play --bots "PurpleWave" "CherryPi" --show_all

**Note**: If you are running Docker Toolbox, and automatical IP address discovery
for Docker machine does not work, you may need run bots like that:

    $ scbw.play --bots "PurpleWave" "CherryPi" --show_all --vnc_host 192.168.99.100

where the 192.168.99.100 is address of your VM where docker machine is running.

## Headless play

Simply add `--headless` option.

## Play against bot

    $ scbw.play --bots "PurpleWave" --human

Select a map, specify your race, and wait for bot(s) to join the game :)

You can put the RealVNC client to fullscreen and play comfortably.

(Although you might want to change your screen resolution to 800x600)

The GUI is going to be probably slower than normal game due to streaming via VNC.

### Play on the host

(more advanced)

#### Two computers

It is however possible to play the game on the host.

You will need two computers connected via a LAN network, one Windows (server, human player)
and one Linux (client, where the bot plays).

Create the game as a human player, and then run

    $ scbw.play --bots "PurpleWave" --opt "--net host"

This will bind the StarCraft ports to the host machine instead of virtual
network `sc_net`. (That's also why you need two computers).

This client was tested on linux only however, there might be
some problems on other OS (due to other OSes not having X server).

#### One computer

## Stop games that failed to finish

Stop all running games in docker containers (container names always begin with `GAME`)

    $  docker stop $(docker ps -a -f NAME=GAME)

## (Re)install newer/specific version

Just run

    $ pip install scbw==XXX
    $ scbw.play --install

## Development

### Add your own bot

Place your bot to `--bot_dir` directory. Some of these are inspired by [SSCAIT rules](http://sscaitournament.com/index.php?action=rules).

Use this structure:

- **/AI/** - put your bot binaries here.

- **/read/** - folder where you can put your config files, initial opponent modelling etc.

  It's contents may be overwritten. After running games contents of the write folder can be copied here, see below.

- **/write/** - folder where bot can write.

    Note that `sc-docker` creates subdirectories in write folder, for each game it's own. If flag `--read_overwrite` is enabled, then the contents of the *write/GAME_xxx* folder will be copied to the *read* folder.

- **/bot.json** - bot configuration. Minimal config is following:

        {
          "name": "NEW BOT",
          "race": "Terran",
          "botType": "JAVA_MIRROR",
        }

    `name` must match `[a-zA-Z0-9_][a-zA-Z0-9_. -]{0,40}`

    `race` can be one of {`Terran`, `Zerg`, `Protoss`, `Random`}.

    `botType` can be one of {`JAVA_JNI`, `JAVA_MIRROR`, `AI_MODULE`, `EXE`, `JYTHON`}

- **/BWAPI.dll** - your own version of BWAPI.dll. Must be in the list of supported BWAPIs, see file `bwapi.py`. You can quickly check if `$ md5sum BWAPI.dll` is some of these:

      4.2.0   2f6fb401c0dcf65925ee7ad34dc6414a
      4.1.2   1364390d0aa085fba6ac11b7177797b0
      4.0.1b  84f413409387ae80a4b4acc51fed3923
      3.7.5   5e590ea55c2d3c66a36bf75537f8655a
      3.7.4   6e940dc6acc76b6e459b39a9cdd466ae

- **/supplementalAI/** - additional files that will be copied to *AI*.

-- **/supplementalRead/** - additional files that will be coped to *read*, ie. configuration files.

Now you should be able to play game:

    $ scbw.play --bots "NEW BOT" "krasi0"

### Developing sc-docker

If you update images, you can rebuild them locally:

    $ cd docker; ./build_images.sh

(or you can use power shell script `docker/build_images.ps1`)

To install develeopment version of the package, use

    $ pip install -e .

in the project root. Now you can call all the `scbw.play` scripts,
and it should call the current source code version (see `pip` for more details).
