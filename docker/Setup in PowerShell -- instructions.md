The guide: how to set up ByteKeeper's sc-docker in Windows PowerShell -- step-by-step instructions
======================================================================================

Note: this guide is intended for Windows installations mainly. Changes for Mac installations will be pointed out along the way. The guide is not guaranteed to work for all Linux versions, despite a few successes. Also, a proper installation of docker is assumed here and should be done first before any of the commands/actions contained in this guide is attempted. For more details on how to install a docker, please see: https://github.com/basil-ladder/sc-docker/blob/master/INSTALL.md


Optional:
Do `pip uninstall scbw` if you have installed `scbw` previously to avoid potential conflicts.

Steps:

0. Download jre-8u192-windows-i586.tar.gz and move it to the `sc-docker\docker` folder
https://www.oracle.com/technetwork/es/java/javase/downloads/jre8-downloads-2133155.html?printOnly=1
  The use of `openjdk` is not advised here as it is much slower.

1. In Windows PowerShell (it is suggested that you run PowerShell in administrator mode), cd to this folder: `sc-docker\docker`; For Mac users, do the same thing in the Terminal app.

2. Open the file `sc-docker\docker\build_images.ps1` and do all commands listed there one at a time. Running all the commands at once may lead to the following message: `Some containers exited prematurely, please check logs`. And you'll likely see no error logs, as all the containers hold only empty folders. The suggested steps of running these commands are:

    2.1) Do the following 4 commands one at a time.
    ```
    docker build -f dockerfiles/wine.dockerfile  -t starcraft:wine   .
    docker build -f dockerfiles/bwapi.dockerfile -t starcraft:bwapi  .
    docker build -f dockerfiles/play.dockerfile  -t starcraft:play   .
    docker build -f dockerfiles/java.dockerfile  -t starcraft:java   .
    ```

    2.2) Mac users: skip this step.
    ```
    Push-Location ../scbw/local_docker
    ```

    2.3) Mac users: skip this step. Instead, download the file `starcraft.zip` from
    http://files.theabyss.ru/sc/starcraft.zip and move it to `sc-docker\scbw\local-docker`.
    ```
    if (!(Test-Path starcraft.zip))
    {
        Invoke-WebRequest 'http://files.theabyss.ru/sc/starcraft.zip' -OutFile starcraft.zip
    }
    ```

    2.4) Mac users: please cd to `sc-docker\scbw\local-docker` first.
    ```
    docker build -f game.dockerfile  -t "starcraft:game" .
    ```

    2.5) Mac users: skip this step.
    ```
    Pop-Location
    ```

3. Do `pip install wheel`
4. Navigate one level up to `sc-docker`, Do `py setup.py bdist_wheel` or `python3 setup.py bdist_wheel` depending on how your Python is setup. For Mac users: use the latter (`python3...`).
5. Do `pip3 install dist/scbw-1.0.4_BK-py3-none-any.whl`
6. When launching a game, append `--docker_image starcraft:game`
An example command may look like this:
`scbw.play --bots "Hao Pan" "Martin Rooijackers" --headless --timeout 630 --read_overwrite --game_speed 0 --map "sscai/(4)Fighting Spirit.scx" --docker_image starcraft:game`
Failure of appending the command may result in the original image (`starcraft:game-1.0.4`) being used.
