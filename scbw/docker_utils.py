import distutils.dir_util
import distutils.errors
import logging
import os
import os.path
import re
import shutil
import subprocess
import time
from pprint import pformat
from typing import List, Optional, Callable, Dict, Any

import docker
import docker.errors
import docker.types

from scbw.error import ContainerException, DockerException, GameException, RealtimeOutedException
from scbw.game_type import GameType
from scbw.player import BotPlayer, HumanPlayer, Player
from scbw.utils import random_string
from scbw.vnc import launch_vnc_viewer

logger = logging.getLogger(__name__)
# disable docker package spam logging
logging.getLogger('urllib3.connectionpool').propagate = False

docker_client = docker.from_env()

DOCKER_STARCRAFT_NETWORK = "sc_net"
SUBNET_CIDR = "172.18.0.0/16"
BASE_VNC_PORT = 5900
VNC_HOST = "localhost"
APP_DIR = "/app"
LOG_DIR = f"{APP_DIR}/logs"
SC_DIR = f"{APP_DIR}/sc"
BWTA_DIR = f"{APP_DIR}/bwta"
BWAPI_DIR = f"{APP_DIR}/bwapi"
BOT_DIR = f"{APP_DIR}/bot"
MAP_DIR = f"{SC_DIR}/maps"
ERRORS_DIR = f"{SC_DIR}/Errors"
BWAPI_DATA_DIR = f"{SC_DIR}/bwapi-data"
BWAPI_DATA_BWTA_DIR = f"{BWAPI_DATA_DIR}/BWTA"
BWAPI_DATA_BWTA2_DIR = f"{BWAPI_DATA_DIR}/BWTA2"
BOT_DATA_SAVE_DIR = f"{BWAPI_DATA_DIR}/save"
BOT_DATA_READ_DIR = f"{BWAPI_DATA_DIR}/read"
BOT_DATA_WRITE_DIR = f"{BWAPI_DATA_DIR}/write"
BOT_DATA_AI_DIR = f"{BWAPI_DATA_DIR}/AI"
BOT_DATA_LOGS_DIR = f"{BWAPI_DATA_DIR}/logs"

EXIT_CODE_REALTIME_OUTED = 2
MAX_TIME_RUNNING_SINGLE_CONTAINER = 70

try:
    from subprocess import DEVNULL  # py3k
except ImportError:
    DEVNULL = open(os.devnull, "wb")


def ensure_docker_can_run() -> None:
    """
    :raises docker.errors.ContainerError
    :raises docker.errors.ImageNotFound
    :raises docker.errors.APIError
    """
    logger.info("checking docker can run")
    version = docker_client.version()["ApiVersion"]
    docker_client.containers.run("hello-world")
    logger.debug(f"using docker API version {version}")


def ensure_local_net(
        network_name: str = DOCKER_STARCRAFT_NETWORK,
        subnet_cidr: str = SUBNET_CIDR
) -> None:
    """
    Create docker local net if not found.

    :raises docker.errors.APIError
    """
    logger.info(f"checking whether docker has network {network_name}")
    ipam_pool = docker.types.IPAMPool(subnet=subnet_cidr)
    ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
    networks = docker_client.networks.list(names=DOCKER_STARCRAFT_NETWORK)
    output = networks[0].short_id if networks else None
    if not output:
        logger.info("network not found, creating ...")
        output = docker_client.networks.create(DOCKER_STARCRAFT_NETWORK, ipam=ipam_config).short_id
    logger.debug(f"docker network id: {output}")


def check_for_game_image(image_name: str) -> None:
    try:
        docker_client.images.get(image_name)
    except docker.errors.ImageNotFound:
        logger.error(f"please make sure to have pulled or built the image {image_name}")
    except docker.errors.APIError:
        pass
    logger.info(f"docker image {image_name} present.")


def check_dockermachine() -> bool:
    """
    Checks that docker-machine is available on the computer

    :raises FileNotFoundError if docker-machine is not present
    """
    logger.debug("checking docker-machine presence")
    # noinspection PyBroadException
    try:
        out = subprocess \
            .check_output(["docker-machine", "version"]) \
            .decode("utf-8") \
            .replace("docker-machine.exe", "") \
            .replace("docker-machine", "") \
            .strip()
        logger.debug(f"using docker machine version {out}")
        return True
    except Exception:
        logger.debug(f"docker machine not present")
        return False


def dockermachine_ip() -> Optional[str]:
    """
    Gets IP address of the default docker machine
    Returns None if no docker-machine executable
    in the PATH and if there no Docker machine
    with name default present
    """
    if not check_dockermachine():
        return None

    # noinspection PyBroadException
    try:
        out = subprocess.check_output(['docker-machine', 'ip'])
        return out.decode("utf-8").strip()
    except Exception:
        logger.debug(f"docker machine not present")
        return None


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
        seed_override: str,
        timeout: Optional[int],
        timeout_at_frame: Optional[int],
        hide_names: bool,
        random_names: bool,
        drop_players: bool,
        allow_input: bool,
        auto_launch: bool,

        # mount dirs
        game_dir: str,
        bot_dir: str,
        map_dir: str,
        bwapi_data_bwta_dir: str,
        bwapi_data_bwta2_dir: str,

        vnc_base_port: int,
        vnc_host: int,
        capture_movement: bool,

        # docker
        docker_image: str,
        nano_cpus: Optional[int],
        mem_limit: Optional[str]
) -> None:
    """
    :raises docker,errors.APIError
    :raises DockerException
    """
    container_name = f"{game_name}_{nth_player}_{player.name.replace(' ', '_')}"

    log_dir = f"{game_dir}/{game_name}/logs_{nth_player}"
    crashes_dir = f"{game_dir}/{game_name}/crashes_{nth_player}"
    os.makedirs(log_dir, mode=0o777, exist_ok=True)  # todo: proper mode
    os.makedirs(crashes_dir, mode=0o777, exist_ok=True)  # todo: proper mode

    volumes = {
        xoscmounts(log_dir): {"bind": LOG_DIR, "mode": "rw"},
        xoscmounts(map_dir): {"bind": MAP_DIR, "mode": "rw"},
        xoscmounts(crashes_dir): {"bind": ERRORS_DIR, "mode": "rw"},
        xoscmounts(bwapi_data_bwta_dir): {"bind": BWAPI_DATA_BWTA_DIR, "mode": "rw"},
        xoscmounts(bwapi_data_bwta2_dir): {"bind": BWAPI_DATA_BWTA2_DIR, "mode": "rw"},
    }

    ports = {}
    if not headless:
        ports.update({"5900/tcp": vnc_base_port + nth_player})

    env = dict(
        PLAYER_NAME=player.name if not random_names else random_string(8),
        PLAYER_RACE=player.race.value,
        NTH_PLAYER=nth_player,
        NUM_PLAYERS=num_players,
        GAME_NAME=game_name,
        MAP_NAME=f"/app/sc/maps/{map_name}",
        GAME_TYPE=game_type.value,
        SPEED_OVERRIDE=game_speed,
        SEED_OVERRIDE=seed_override,
        HIDE_NAMES="1" if hide_names else "0",
        DROP_PLAYERS="1" if drop_players else "0",

        TM_LOG_RESULTS=f"../logs/scores.json",
        TM_LOG_FRAMETIMES=f"../logs/frames.csv",
        TM_LOG_UNIT_EVENTS=f"../logs/unit_events.csv",
        TM_SPEED_OVERRIDE=game_speed,
        TM_SEED_OVERRIDE=seed_override,
        TM_ALLOW_USER_INPUT="1" if isinstance(player, HumanPlayer) or allow_input else "0",
        TM_TIME_OUT_AT_FRAME=timeout_at_frame or "-1",

        EXIT_CODE_REALTIME_OUTED=EXIT_CODE_REALTIME_OUTED,
        CAPTURE_MOUSE_MOVEMENT="1" if capture_movement else "0",
        HEADFUL_AUTO_LAUNCH="1" if auto_launch else "0",

        JAVA_DEBUG="0"
    )

    if timeout is not None:
        env["PLAY_TIMEOUT"] = timeout

    if isinstance(player, BotPlayer):
        # Only mount write directory, read and AI
        # are copied from the bot directory in proper places in bwapi-data
        bot_data_write_dir = f"{game_dir}/{game_name}/write_{nth_player}/"
        os.makedirs(bot_data_write_dir, mode=0o777, exist_ok=True)  # todo: proper mode
        volumes.update({
            xoscmounts(bot_data_write_dir): {"bind": BOT_DATA_WRITE_DIR, "mode": "rw"},
            xoscmounts(player.bot_dir): {"bind": BOT_DIR, "mode": "ro"},
        })
        env["BOT_FILE"] = player.bot_basefilename
        env["BOT_BWAPI"] = player.bwapi_version

        env["JAVA_DEBUG"] = "0"
        env["JAVA_DEBUG_PORT"] = ""
        env["JAVA_OPTS"] = ""

        command = ["/app/play_bot.sh"]
        if player.meta.javaDebugPort is not None:
            ports.update({f"{player.meta.javaDebugPort}/tcp": player.meta.javaDebugPort})
            env["JAVA_DEBUG"] = "1"
            env["JAVA_DEBUG_PORT"] = player.meta.javaDebugPort
        if player.meta.javaOpts is not None:
            env["JAVA_OPTS"] = player.meta.javaOpts
        if player.meta.port is not None:
            if isinstance(player.meta.port, int) or player.meta.port.isdigit():
                ports.update({str(player.meta.port) + '/tcp': int(player.meta.port)})
            else:
                forward, local = [int(x) for x in player.meta.port.split(':')]
                ports.update({str(local) + '/tcp': forward})
    else:
        command = ["/app/play_human.sh"]

    is_server = nth_player == 0

    entrypoint_opts = ["--headful"]
    if headless:
        entrypoint_opts = [
            "--game", game_name, "--name", player.name,
            "--race", player.race.value, "--lan"
        ]
        if is_server:
            entrypoint_opts += ["--host", "--map", f"/app/sc/maps/{map_name}"]
        else:
            entrypoint_opts += ["--join"]
    command += entrypoint_opts

    logger.debug(
        "\n"
        f"docker_image={docker_image}\n"
        f"command={pformat(command, indent=4)}\n"
        f"name={container_name}\n"
        f"detach={True}\n"
        f"environment={pformat(env, indent=4)}\n"
        f"volumes={pformat(volumes, indent=4)}\n"
        f"network={DOCKER_STARCRAFT_NETWORK}\n"
        f"ports={ports}\n"
        f"nano_cpus={nano_cpus}\n"
        f"mem_limit={mem_limit}\n"
    )

    container = docker_client.containers.run(
        docker_image,
        command=command,
        name=container_name,
        detach=True,
        environment=env,
        volumes=volumes,
        network=DOCKER_STARCRAFT_NETWORK,
        ports=ports,
        nano_cpus=nano_cpus,
        mem_limit=mem_limit or None
    )
    if container:
        container_id = running_containers(container_name)
        logger.info(f"launched {player}")
        logger.debug(f"container name = '{container_name}', container id = '{container_id}'")
    else:
        raise DockerException(f"could not launch {player} in container {container_name}")


def running_containers(name_filter: str) -> List[str]:
    """
    :raises docker.exceptions.APIError
    """
    return [container.short_id for container in
            docker_client.containers.list(filters={"name": name_filter})]


def remove_game_containers(name_filter: str) -> None:
    """
    :raises docker.exceptions.APIError
    """
    for container in docker_client.containers.list(filters={"name": name_filter}, all=True):
        container.stop()
        container.remove()


def container_exit_code(container_id: str) -> Optional[int]:
    """
    :raises docker.errors.NotFound
    :raises docker.errors.APIError
    """
    container = docker_client.containers.get(container_id)
    return container.wait()["StatusCode"]


def launch_game(
        players: List[Player],
        launch_params: Dict[str, Any],
        show_all: bool,
        read_overwrite: bool,
        wait_callback: Callable
) -> None:
    """
    :raises DockerException, ContainerException, RealtimeOutedException
    """
    if not players:
        raise GameException("at least one player must be specified")

    game_dir = launch_params["game_dir"]
    game_name = launch_params["game_name"]

    if os.path.exists(f"{game_dir}/{game_name}"):
        logger.info(f"removing existing game results of {game_name}")
        shutil.rmtree(f"{game_dir}/{game_name}")

    for nth_player, player in enumerate(players):
        launch_image(player, nth_player=nth_player, num_players=len(players), **launch_params)

    logger.debug("checking if game has launched properly...")
    time.sleep(1)
    start_containers = running_containers(game_name + "_")
    if len(start_containers) != len(players):
        raise DockerException("some containers exited prematurely, please check logs")

    if not launch_params["headless"]:
        for index, player in enumerate(players if show_all else players[:1]):
            port = launch_params["vnc_base_port"] + index
            host = launch_params["vnc_host"]
            logger.info(f"launching vnc viewer for {player} on address {host}:{port}")
            launch_vnc_viewer(host, port)

        logger.info("\n"
                    "In headful mode, you must specify and start the game manually.\n"
                    "Select the map, wait for bots to join the game "
                    "and then start the game.")

    logger.info(f"waiting until game {game_name} is finished...")
    running_time = time.time()
    while True:
        containers = running_containers(game_name)
        if len(containers) == 0:  # game finished
            break
        if len(containers) >= 2:  # update the last time when there were multiple containers
            running_time = time.time()
        if len(containers) == 1 and time.time() - running_time > MAX_TIME_RUNNING_SINGLE_CONTAINER:
            raise ContainerException(
                f"One lingering container has been found after single container "
                f"timeout ({MAX_TIME_RUNNING_SINGLE_CONTAINER} sec), the game probably crashed.")
        logger.debug(f"waiting. {containers}")
        wait_callback()

    containers = docker_client.containers.list(filters={"name": game_name}, all=True)
    exit_codes = [container_exit_code(container.short_id) for container in containers]
    logger.debug(f"Exit codes: {exit_codes}")

    # remove containers before throwing exception
    logger.debug("removing game containers")
    remove_game_containers(game_name)

    if any(exit_code == EXIT_CODE_REALTIME_OUTED for exit_code in exit_codes):
        raise RealtimeOutedException(f"some of the game containers has realtime outed.")
    if any(exit_code == 1 for exit_code in exit_codes):
        raise ContainerException(f"some of the game containers has finished with error exit code.")

    if read_overwrite:
        logger.info("overwriting bot files")
        for nth_player, player in enumerate(players):
            if isinstance(player, BotPlayer):
                logger.debug(f"overwriting files for {player}")
                distutils.dir_util.copy_tree(
                    f"{game_dir}/{game_name}/write_{nth_player}",
                    player.read_dir
                )
