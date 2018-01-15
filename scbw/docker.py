import logging
import os
import subprocess
import time
from distutils.dir_util import copy_tree
from typing import List, Optional

from .game import GameType
from .player import BotPlayer, Player
from .vnc import launch_vnc_viewer

logger = logging.getLogger(__name__)

DOCKER_STARCRAFT_NETWORK = "sc_net"

try:
    from subprocess import DEVNULL # py3k
except ImportError:
    DEVNULL = open(os.devnull, 'wb')


def check_docker_version():
    logger.info("checking docker version")
    try:
        out = subprocess.check_output(["docker", "version", "--format", "'{{.Server.APIVersion}}'"])
    except Exception as e:
        raise Exception("An error occurred while trying to call `docker version`,"
                        " did you install docker?")
    logger.debug(f"Using docker API version {out}")


def check_docker_can_run():
    logger.info("checking docker can run")
    try:
        out = subprocess.check_output(["docker", "run", "hello-world"])
    except Exception as e:
        raise Exception(
            "An error occurred while trying to call `docker run hello-world`, "
            "do you have suffiecient rights to run sudo?")

    if b"Hello" not in out:
        raise Exception(
            f"Docker did not run properly - could'nt find 'Hello' in hello-world run, found {out}")


def check_docker_has_local_net() -> bool:
    logger.info(f"checking docker has network {DOCKER_STARCRAFT_NETWORK}")
    try:
        out = subprocess.check_output(
            ["docker", "network", "ls", "-f", f"name={DOCKER_STARCRAFT_NETWORK}", "-q"])
    except Exception as e:
        raise Exception(
            f"An error occurred while trying to call `docker network ls -f name={DOCKER_STARCRAFT_NETWORK} -q`")

    logger.debug(f"docker network id: {out}")
    return bool(out)


def create_local_net():
    try:
        logger.info(f"creating docker local net {DOCKER_STARCRAFT_NETWORK}")
        out = subprocess.check_output(
            ["docker", "network", "create", "--subnet=172.18.0.0/16", DOCKER_STARCRAFT_NETWORK])
    except Exception as e:
        raise Exception(
            f"An error occurred while trying to call `docker network create --subnet=172.18.0.0/16 {DOCKER_STARCRAFT_NETWORK}`")

    logger.debug(f"docker network id: {out}")


def check_docker_requirements():
    check_docker_version()
    check_docker_can_run()
    check_docker_has_local_net() or create_local_net()


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
           "--privileged",

           "--name", f"{game_name}_{nth_player}_{player.name.replace(' ', '_')}",

           "--volume", f"{log_dir}:{LOG_DIR}:rw",
           "--volume", f"{bot_dir}:{BOT_DIR}:ro",
           "--volume", f"{map_dir}:{MAP_DIR}:rw",
           "--volume", f"{bwapi_data_bwta_dir}:{BWAPI_DATA_BWTA_DIR}:rw",
           "--volume", f"{bwapi_data_bwta2_dir}:{BWAPI_DATA_BWTA2_DIR}:rw",

           "--net", DOCKER_STARCRAFT_NETWORK]

    if docker_opts:
        cmd += docker_opts

    if not headless:
        cmd += ["-p", f"{vnc_base_port+nth_player}:5900"]

    if isinstance(player, BotPlayer):
        bot_data_write_dir = f"{player.base_dir}/write/{game_name}_{nth_player}"
        os.makedirs(bot_data_write_dir, mode=0o777)  # todo: proper mode
        cmd += ["--volume", f"{bot_data_write_dir}:{BOT_DATA_WRITE_DIR}:rw"]

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
        raise Exception(
            f"could not launch {player} in container {game_name}_{nth_player}_{player.name}")


def running_containers(name_prefix):
    out = subprocess.check_output(f'docker ps -f "name={name_prefix}" -q', shell=True)
    containers = [container.strip() for container in out.decode("utf-8").split("\n") if
                  container != ""]
    logger.debug(f"running containers: {containers}")
    return containers


def stop_containers(name_prefix: str):
    containers = running_containers(name_prefix)
    subprocess.call(['docker', 'stop'] + containers, stdout=DEVNULL)


def launch_game(players, launch_params, show_all, read_overwrite):
    logger.info(f"Logs can be found in {launch_params['log_dir']}"
                f"/GAME_{launch_params['game_name']}_*")

    for i, player in enumerate(players):
        launch_image(player, nth_player=i, num_players=len(players), **launch_params)

    logger.info("Checking if game has launched properly...")
    time.sleep(2)
    containers = running_containers(launch_params['game_name'])
    if len(containers) != len(players):
        raise Exception("Some containers exited prematurely, please check logs")

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

    if read_overwrite:
        logger.info("Overwriting bot files")
        for nth_player, player in enumerate(players):
            if isinstance(player, BotPlayer):
                logger.debug(f"Overwriting files for {player}")
                copy_tree(f"{player.write_dir}/{launch_params['game_name']}_{nth_player}",
                          player.read_dir)
