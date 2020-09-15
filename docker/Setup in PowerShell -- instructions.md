The guide: how to set up ByteKeeper's sc-docker for the BASIL ladder in Windows PowerShell -- step-by-step instructions
======================================================================================

Notes 
* This guide is intended for Windows installations mainly. The guide is applicable for Mac installations with a few changes which will be pointed out along the way. The guide is not guaranteed to work for all Linux versions, despite a few successes. 

* This guide is verified to work with the `wine5` branch as of 15/Sep/2020. Using the `master` branch may cause the ```Game has crashed!``` message after running a game.

* A proper installation of a docker is assumed here and should be done first before attempting any of the commands/actions in this guide. For more details on how to install a docker, please see: https://github.com/basil-ladder/sc-docker/blob/master/INSTALL.md

* For Windows users, you may skip steps 1-2 and instead execute the `build_images.ps1` PowerShell script found in the `sc-docker\docker` folder. If any error message pops up, please do steps 1-2 as described below to get an idea on where it really went wrong.

* Also for Windows users, before you start, please make sure that **all** the files inside the `sc-docker\docker\scripts` folder have the LF line termination type, instead of the CRLF one. For details on how to convert CRLF to LF, see https://stackoverflow.com/questions/27810758/how-to-replace-crlf-with-lf-in-a-single-file
Using Notepad++ proved to be working for the purposes here.

* It is normal to see this message during the installation process:
`SECURITY WARNING: You are building a Docker image from Windows against a non-Windows Docker host. All files and directories added to build context will have '-rwxr-xr-x' permissions. It is recommended to double check and reset permissions for sensitive files and directories.`
For some explanations, please see: https://github.com/moby/moby/issues/20397

Optional steps:
* Do `pip uninstall scbw` if you have installed `scbw` previously to avoid potential conflicts.
* Do "Reset to factory defaults..." in docker if there are sc-docker-related images previously installed (e.g., the StarCraft game image). Proceed with caution if you have other images which are not related to sc-docker.

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
6. An example command to run a game may look like this:
`scbw.play --bots "Hao Pan" "Martin Rooijackers" --headless --timeout 630 --read_overwrite --game_speed 0 --map "sscai/(4)Fighting Spirit.scx"`
7. For Windows users: do `scbw.play --install` if you see `docker.errors.NotFound: 404 Client Error: Not Found ("network sc_net not found")` after launching a game.
