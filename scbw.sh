#!/bin/bash

docker image inspect starcraft:game > /dev/null
if [ $? -ne 0 ]; then
	docker run -v /var/run/docker.sock:/var/run/docker.sock -e STARCRAFT_UID=$(id -u) scbw /bin/bash -c "cd scbw/docker; ./build_images.sh"
	docker run -v /var/run/docker.sock:/var/run/docker.sock scbw --install
fi

mkdir ~/.scbw 2> /dev/null
docker run -it --rm -v /var/run/docker.sock:/var/run/docker.sock -v ~/.scbw:/root/.scbw scbw scbw.play "$@"
