docker build -f dockerfiles/wine.dockerfile  -t starcraft:wine   .
docker build -f dockerfiles/bwapi.dockerfile -t starcraft:bwapi  .
docker build -f dockerfiles/play.dockerfile  -t starcraft:play   .
docker build -f dockerfiles/java.dockerfile  -t starcraft:java   .

Push-Location ../scbw/local_docker
if (!(Test-Path starcraft.zip))
{
    Invoke-WebRequest 'http://files.theabyss.ru/sc/starcraft.zip' -OutFile starcraft.zip
}

docker build -f game.dockerfile  -t "starcraft:game" .
Pop-Location
