How to set up ByteKeeper's sc-docker in Windows PowerShell. Step-by-step instructions:

Optional:
Do `pip uninstall scbw` if you have installed `scbw` previously to avoid potential conflict.

Steps:
0) Download jre-8u192-windows-i586.tar.gz and move it to the `sc-docker-master\docker` folder
https://www.oracle.com/technetwork/es/java/javase/downloads/jre8-downloads-2133155.html?printOnly=1
Use of openjdk is not advised here as it is much slower.
1) In Windows PowerShell, cd to this folder: `sc-docker-master\docker`
2) Open the file `sc-docker-master\docker\build_images.ps1` and do all commands listed there in PowerShell (you may want to run PowerShell in administrator mode).

Please do commands one at a time. Suggested segmentation:

2.1) 
```
docker build -f dockerfiles/wine.dockerfile  -t starcraft:wine   .
docker build -f dockerfiles/bwapi.dockerfile -t starcraft:bwapi  .
docker build -f dockerfiles/play.dockerfile  -t starcraft:play   .
docker build -f dockerfiles/java.dockerfile  -t starcraft:java   .
```

2.2) 
```
Push-Location ../scbw/local_docker
```

2.3)
```
if (!(Test-Path starcraft.zip))
{
    Invoke-WebRequest 'http://files.theabyss.ru/sc/starcraft.zip' -OutFile starcraft.zip
}
```

2.4)
```
docker build -f game.dockerfile  -t "starcraft:game" .
```

2.5)
```
Pop-Location
```

Failure to do so would cause the following error message when doing step 6):
`Some containers exited prematurely, please check logs`

And you'll likely see no error log, as every container is empty.

3) Do `pip install wheel`
4) Navigate one level up to `sc-docker-master`, Do `py setup.py bdist_wheel` or `python3 setup.py bdist_wheel` depending on how your Python is setup.
5) Do `pip3 install dist/scbw-1.0.4-py3-none-any.whl`
6) When launching a game, append `--docker_image starcraft:game`
An example command would look like this:
`scbw.play --bots "Hao Pan" "Martin Rooijackers" --headless --timeout 630 --read_overwrite --game_speed 0 --map "sscai/(4)Fighting Spirit.scx" --docker_image starcraft:game`
If you don't do this, the original image, `starcraft:game-1.0.4`, will be used.
