import logging
import os
import re
import subprocess
import sys
import time
from distutils.dir_util import copy_tree
from os.path import exists, abspath, dirname
from typing import List, Optional, Callable

from .defaults import *
from .error import DockerException
from .game_type import GameType
from .player import BotPlayer, Player
from .utils import download_file
from .vnc import launch_vnc_viewer

logger = logging.getLogger(__name__)

DOCKER_STARCRAFT_NETWORK = "sc_net"

try:
    from subprocess import DEVNULL  # py3k
except ImportError:
    DEVNULL = open(os.devnull, 'wb')


def check_docker_version():
    logger.info("checking docker version")
    try:
        out = subprocess.check_output(["docker", "version", "--format", "'{{.Server.APIVersion}}'"])
    except Exception:
        raise DockerException("An error occurred while trying to call `docker version`,"
                              " did you install docker?")
    logger.debug(f"Using docker API version {out}")


def check_docker_can_run():
    logger.info("checking docker can run")
    try:
        out = subprocess.check_output(["docker", "run", "hello-world"])
    except Exception:
        raise DockerException(
            "An error occurred while trying to call `docker run hello-world`, "
            "do you have sufficient rights to run sudo?")

    if b"Hello" not in out:
        raise DockerException(
            f"Docker did not run properly - could'nt find 'Hello' in hello-world run, found {out}")


def check_docker_has_local_net() -> bool:
    logger.info(f"checking docker has network {DOCKER_STARCRAFT_NETWORK}")
    try:
        out = subprocess.check_output(
            ["docker", "network", "ls", "-f", f"name={DOCKER_STARCRAFT_NETWORK}", "-q"])
    except Exception:
        raise DockerException(
            f"An error occurred while trying to call `docker network ls -f name={DOCKER_STARCRAFT_NETWORK} -q`")

    logger.debug(f"docker network id: {out}")
    return bool(out)


def create_local_net():
    try:
        logger.info(f"creating docker local net {DOCKER_STARCRAFT_NETWORK}")
        out = subprocess.check_output(
            ["docker", "network", "create", "--subnet=172.18.0.0/16", DOCKER_STARCRAFT_NETWORK])
    except Exception:
        raise DockerException(
            f"An error occurred while trying to call `docker network create --subnet=172.18.0.0/16 {DOCKER_STARCRAFT_NETWORK}`")

    logger.debug(f"docker network id: {out}")


def check_docker_has_local_image(image: str) -> bool:
    try:
        logger.info(f"checking if there is local image {image}")
        out = subprocess.check_output(["docker", "images", "-q", image])

    except Exception:
        raise DockerException(
            f"An error occurred while trying to call `docker images -q {image}`")

    logger.debug(f"docker image id: {out}")
    return bool(out)


def create_local_image(image: str):
    try:
        # first copy all docker files we will need
        # for building image to somewhere we can write
        pkg_docker_dir = f'{abspath(dirname(__file__))}/local_docker'
        base_dir = SCBW_BASE_DIR + "/docker"

        logger.info(f"creating docker local image")
        logger.info(f"copying files from {pkg_docker_dir} to {base_dir}")
        copy_tree(pkg_docker_dir, base_dir)

        # pull java parent image
        logger.info(f"pulling image {SC_PARENT_IMAGE}, this may take a while...")
        if subprocess.call(['docker', 'pull', SC_PARENT_IMAGE], stdout=sys.stderr.buffer) != 0:
            raise DockerException(
                f"an error occurred while calling `docker pull {SC_PARENT_IMAGE}`")
        if subprocess.call(['docker', 'tag', SC_PARENT_IMAGE, SC_JAVA_IMAGE], stdout=sys.stderr.buffer) != 0:
            raise DockerException(
                f"an error occurred while calling `docker tag {SC_PARENT_IMAGE} {SC_JAVA_IMAGE}`")

        # download starcraft.zip
        starcraft_zip_file = f"{base_dir}/starcraft.zip"
        if not exists(starcraft_zip_file):
            logger.info(f"downloading starcraft.zip to {starcraft_zip_file}")
            download_file('http://files.theabyss.ru/sc/starcraft.zip', starcraft_zip_file)

        # build
        logger.info(f"building local image {image}, this may take a while...")
        if subprocess.call(['docker', 'build',
                            '-f', 'game.dockerfile',
                            '-t', image, '.'],
                           cwd=base_dir, stdout=sys.stderr.buffer) != 0:
            raise DockerException()

        logger.info(f"successfully built image {image}")

    except Exception:
        raise DockerException(f"An error occurred while trying to build local image")


def remove_game_image(image_name):
    has_image = check_output(f"docker images {image_name} -q", shell=True)
    if has_image:
        call(f"docker rmi --force {image_name}", shell=True)


def check_output(*args, **kwargs):
    try:
        return subprocess.check_output(*args, **kwargs)
    except subprocess.CalledProcessError:
        print(f"Failed calling {args} {kwargs}")
        sys.exit(1)


def call(*args, **kwargs):
    code = subprocess.call(*args, **kwargs)
    if code != 0:
        print(f"Failed calling {args} {kwargs}")
        sys.exit(1)


def check_docker_requirements(image: str):
    check_docker_version()
    check_docker_can_run()
    check_docker_has_local_net() or create_local_net()
    check_docker_has_local_image(image) or create_local_image(image)


BASE_VNC_PORT = 5900
APP_DIR = "/app"
LOG_DIR = f"{APP_DIR}/logs"
SC_DIR = f"{APP_DIR}/sc"
BWTA_DIR = f"{APP_DIR}/bwta"
BWAPI_DIR = f"{APP_DIR}/bwapi"
BOT_DIR = f"{APP_DIR}/bots"
MAP_DIR = f"{SC_DIR}/maps"
BWAPI_DATA_DIR = f"{SC_DIR}/bwapi-data"
BWAPI_DATA_BWTA_DIR = f"{BWAPI_DATA_DIR}/BWTA"
BWAPI_DATA_BWTA2_DIR = f"{BWAPI_DATA_DIR}/BWTA2"
BOT_DATA_SAVE_DIR = f"{BWAPI_DATA_DIR}/save"
BOT_DATA_READ_DIR = f"{BWAPI_DATA_DIR}/read"
BOT_DATA_WRITE_DIR = f"{BWAPI_DATA_DIR}/write"
BOT_DATA_AI_DIR = f"{BWAPI_DATA_DIR}/AI"
BOT_DATA_LOGS_DIR = f"{BWAPI_DATA_DIR}/logs"


def xoscmounts(host_mount):
    """
    Cross OS compatible mount dirs
    """
    callback_lower_drive_letter = lambda pat: pat.group(1).lower()
    host_mount = re.sub(r"^([a-zA-Z])\:", callback_lower_drive_letter, host_mount)
    host_mount = re.sub(r"^([a-z])", "//\\1", host_mount)
    host_mount = re.sub(r"\\", "/", host_mount)
    return host_mount


def launch_image(
        # players info
        player: Player,
        nth_player: int,
        num_players: int,

        # game settings
        headless: bool,
        game_name: str,
        map_name: str,
        game_type: GameType,
        game_speed: int,
        timeout: Optional[int],

        # mount dirs
        log_dir: str,
        bot_dir: str,
        map_dir: str,
        bwapi_data_bwta_dir: str,
        bwapi_data_bwta2_dir: str,

        vnc_base_port: int,

        # docker
        docker_image: str,
        docker_opts: List[str]):
    #
    cmd = ["docker", "run",

           "-d",
           "--rm",
           "--privileged",

           "--name", f"{game_name}_{nth_player}_{player.name.replace(' ', '_')}",

           "--volume", f"{xoscmounts(log_dir)}:{LOG_DIR}:rw",
           "--volume", f"{xoscmounts(bot_dir)}:{BOT_DIR}:ro",
           "--volume", f"{xoscmounts(map_dir)}:{MAP_DIR}:rw",
           "--volume", f"{xoscmounts(bwapi_data_bwta_dir)}:{BWAPI_DATA_BWTA_DIR}:rw",
           "--volume", f"{xoscmounts(bwapi_data_bwta2_dir)}:{BWAPI_DATA_BWTA2_DIR}:rw",
           ]

    if docker_opts:
        cmd += docker_opts

    # allow for --net override in docker opts
    if "--net" not in docker_opts:
        cmd += ["--net", DOCKER_STARCRAFT_NETWORK]

    if not headless:
        cmd += ["-p", f"{vnc_base_port+nth_player}:5900"]

    if isinstance(player, BotPlayer):
        bot_data_write_dir = f"{player.base_dir}/write/{game_name}_{nth_player}"
        os.makedirs(bot_data_write_dir, mode=0o777, exist_ok=True)  # todo: proper mode
        cmd += ["--volume", f"{xoscmounts(bot_data_write_dir)}:{BOT_DATA_WRITE_DIR}:rw"]

    env = ["-e", f"PLAYER_NAME={player.name}",
           "-e", f"PLAYER_RACE={player.race.value}",
           "-e", f"NTH_PLAYER={str(nth_player)}",
           "-e", f"NUM_PLAYERS={str(num_players)}",
           "-e", f"GAME_NAME={game_name}",
           "-e", f"MAP_NAME=/app/sc/maps/{map_name}",
           "-e", f"GAME_TYPE={game_type.value}",
           "-e", f"SPEED_OVERRIDE={str(game_speed)}"]
    if isinstance(player, BotPlayer):
        env += ["-e", f"BOT_NAME={player.name}",
                "-e", f"BOT_FILE={player.bot_basefilename}"]
    if timeout is not None:
        env += ["-e", f"PLAY_TIMEOUT={timeout}"]

    cmd += env

    cmd += [docker_image]
    if isinstance(player, BotPlayer):
        cmd += ["/app/play_bot.sh"]
    else:
        cmd += ["/app/play_human.sh"]

    entrypoint_opts = []
    is_server = nth_player == 0

    if not headless:
        entrypoint_opts += ["--headful"]
    else:
        entrypoint_opts += ["--game", game_name,
                            "--name", player.name,
                            "--race", player.race.value,
                            "--lan"]

        if is_server:
            entrypoint_opts += ["--host",
                                "--map", f"/app/sc/maps/{map_name}"]
        else:
            entrypoint_opts += ["--join"]

    cmd += entrypoint_opts

    logger.debug(cmd)
    code = subprocess.call(cmd, stdout=DEVNULL)

    if code == 0:
        logger.info(f"launched {player} in container {game_name}_{nth_player}_{player.name}")
    else:
        raise DockerException(
            f"could not launch {player} in container {game_name}_{nth_player}_{player.name}")


def running_containers(name_prefix):
    out = subprocess.check_output(f'docker ps -f "name={name_prefix}" -q', shell=True)
    containers = [container.strip() for container in out.decode("utf-8").split("\n") if
                  container != ""]
    logger.debug(f"running containers: {containers}")
    return containers


def stop_containers(name_prefix: str):
    containers = running_containers(name_prefix)
    subprocess.call(['docker', 'stop'] + containers, stdout=sys.stderr.buffer)


def launch_game(players, launch_params, show_all, read_overwrite,
                wait_callback: Optional[Callable] = None):
    if len(players) == 0:
        raise DockerException("At least one player must be specified")

    for i, player in enumerate(players):
        launch_image(player, nth_player=i, num_players=len(players), **launch_params)

    logger.info("Checking if game has launched properly...")
    time.sleep(2)
    containers = running_containers(launch_params['game_name'])
    if len(containers) != len(players):
        raise DockerException("Some containers exited prematurely, please check logs")

    if not launch_params['headless']:
        time.sleep(1)

        for i, player in enumerate(players if show_all else players[:1]):
            port = launch_params['vnc_base_port'] + i
            logger.info(f"Launching vnc viewer for {player} on port {port}")
            launch_vnc_viewer(port)

        logger.info("\n"
                    "In headful mode, you must specify and start the game manually.\n"
                    "Select the map, wait for bots to join the game "
                    "and then start the game.")

    logger.info("Waiting until game is finished...")
    while len(running_containers(launch_params['game_name'])) > 0:
        time.sleep(3)
        if wait_callback is not None:
            wait_callback()

    if read_overwrite:
        logger.info("Overwriting bot files")
        for nth_player, player in enumerate(players):
            if isinstance(player, BotPlayer):
                logger.debug(f"Overwriting files for {player}")
                copy_tree(f"{player.write_dir}/{launch_params['game_name']}_{nth_player}",
                          player.read_dir)
