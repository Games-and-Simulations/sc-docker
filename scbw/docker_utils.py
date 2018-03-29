import distutils.dir_util
import distutils.errors
import itertools
import logging
import os
import os.path
import re
import subprocess
import time
from typing import List, Optional, Callable, Dict, Any

import docker
import docker.errors
import docker.types
from scbw.defaults import SCBW_BASE_DIR, SC_PARENT_IMAGE, SC_JAVA_IMAGE, SC_BINARY_LINK
from scbw.error import ContainerException, DockerException, GameException, RealtimeOutedException
from scbw.game_type import GameType
from scbw.logs import find_frames, find_logs, find_replays, find_results
from scbw.player import BotPlayer, HumanPlayer, Player
from scbw.utils import download_file
from scbw.vnc import launch_vnc_viewer

logger = logging.getLogger(__name__)
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
BWAPI_DATA_DIR = f"{SC_DIR}/bwapi-data"
BWAPI_DATA_BWTA_DIR = f"{BWAPI_DATA_DIR}/BWTA"
BWAPI_DATA_BWTA2_DIR = f"{BWAPI_DATA_DIR}/BWTA2"
BOT_DATA_SAVE_DIR = f"{BWAPI_DATA_DIR}/save"
BOT_DATA_READ_DIR = f"{BWAPI_DATA_DIR}/read"
BOT_DATA_WRITE_DIR = f"{BWAPI_DATA_DIR}/write"
BOT_DATA_AI_DIR = f"{BWAPI_DATA_DIR}/AI"
BOT_DATA_LOGS_DIR = f"{BWAPI_DATA_DIR}/logs"

EXIT_CODE_REALTIME_OUTED = 2
MAX_TIME_RUNNING_SINGLE_CONTAINER = 20

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


def ensure_local_image(
        local_image: str,
        parent_image: str = SC_PARENT_IMAGE,
        java_image: str = SC_JAVA_IMAGE,
        starcraft_base_dir: str = SCBW_BASE_DIR,
        starcraft_binary_link: str = SC_BINARY_LINK,
) -> None:
    """
    Check if `local_image` is present locally. If it is not, pull parent images and build.
    This includes pulling starcraft binary.

    :raises docker.errors.ImageNotFound
    :raises docker.errors.APIError
    """
    logger.info(f"checking if there is local image {local_image}")
    docker_image = docker_client.images.search(local_image)
    if docker_image and docker_image.short_id is not None:
        logger.info(f"image {local_image} found locally.")
        return

    logger.info("image not found locally, creating...")
    pkg_docker_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "local_docker")
    base_dir = os.path.join(starcraft_base_dir, "docker")
    logger.info(f"copying files from {pkg_docker_dir} to {base_dir}.")
    distutils.dir_util.copy_tree(pkg_docker_dir, base_dir)

    starcraft_zip_file = f"{base_dir}/starcraft.zip"
    if not os.path.exists(starcraft_zip_file):
        logger.info(f"downloading starcraft.zip to {starcraft_zip_file}")
        download_file(starcraft_binary_link, starcraft_zip_file)

    logger.info(f"pulling image {parent_image}, this may take a while...")
    pulled_image = docker_client.images.pull(parent_image)
    pulled_image.tag(java_image)

    logger.info(f"building local image {local_image}, this may take a while...")
    docker_client.images.build(path=base_dir, dockerfile="game.dockerfile", tag=local_image)
    logger.info(f"successfully built image {local_image}")


def remove_game_image(image_name: str) -> None:
    try:
        docker_client.images.get(image_name)
    except docker.errors.ImageNotFound:
        pass
    except docker.errors.APIError:
        logger.error(f"there occurred an error trying to find image {image_name}")
    else:
        docker_client.images.remove(image_name, force=True)
    logger.info(f"docker image {image_name} removed.")


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
        timeout: Optional[int],
        hide_names: bool,
        drop_players: bool,

        # mount dirs
        log_dir: str,
        bot_dir: str,
        map_dir: str,
        bwapi_data_bwta_dir: str,
        bwapi_data_bwta2_dir: str,

        vnc_base_port: int,
        vnc_host: int,

        # docker
        docker_image: str,
        docker_opts: List[str]
) -> None:
    """
    :raises docker,errors.APIError
    :raises DockerException
    """
    container_name = f"{game_name}_{nth_player}_{player.name.replace(' ', '_')}"

    volumes = {
        xoscmounts(log_dir): {"bind": LOG_DIR, "mode": "rw"},
        xoscmounts(map_dir): {"bind": MAP_DIR, "mode": "rw"},
        xoscmounts(bwapi_data_bwta_dir): {"bind": BWAPI_DATA_BWTA_DIR, "mode": "rw"},
        xoscmounts(bwapi_data_bwta2_dir): {"bind": BWAPI_DATA_BWTA2_DIR, "mode": "rw"},
    }

    ports = {}
    if not headless:
        ports.update({"5900/tcp": vnc_base_port + nth_player})

    env = dict(
        PLAYER_NAME=player.name,
        PLAYER_RACE=player.race.value,
        NTH_PLAYER=nth_player,
        NUM_PLAYERS=num_players,
        GAME_NAME=game_name,
        MAP_NAME=f"/app/sc/maps/{map_name}",
        GAME_TYPE=game_type.value,
        SPEED_OVERRIDE=game_speed,
        HIDE_NAMES="1" if hide_names else "0",
        DROP_PLAYERS="1" if drop_players else "0",

        TM_LOG_RESULTS=f"../logs/{game_name}_{nth_player}_results.json",
        TM_LOG_FRAMETIMES=f"../logs/{game_name}_{nth_player}_frames.csv",
        TM_SPEED_OVERRIDE=game_speed,
        TM_ALLOW_USER_INPUT="1" if isinstance(player, HumanPlayer) else "0",

        EXIT_CODE_REALTIME_OUTED=EXIT_CODE_REALTIME_OUTED,

        JAVA_DEBUG="0"
    )

    if isinstance(player, BotPlayer):
        # Only mount write directory, read and AI
        # are copied from the bot directory in proper places in bwapi-data
        bot_data_write_dir = f"{player.bot_dir}/write/{game_name}_{nth_player}"
        os.makedirs(bot_data_write_dir, mode=0o777, exist_ok=True)  # todo: proper mode
        volumes.update({
            xoscmounts(bot_data_write_dir): {"bind": BOT_DATA_WRITE_DIR, "mode": "rw"},
            xoscmounts(player.bot_dir): {"bind": BOT_DIR, "mode": "ro"},
        })
        env["BOT_FILE"] = player.bot_basefilename
        env["BOT_BWAPI"] = player.bwapi_version
        command = ["/app/play_bot.sh"]
        if player.meta.javaDebugPort is not None:
            ports.update({"player.meta.javaDebugPort/tcp": player.meta.javaDebugPort})
            env["JAVA_DEBUG"] = "1"
            env["JAVA_DEBUG_PORT"] = player.meta.javaDebugPort
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
        f"""
        docker_image = {docker_image}
        command={command},
        name={container_name},
        detach={True},
        environment={env},
        privileged={True},
        volumes={volumes},
        network={DOCKER_STARCRAFT_NETWORK},
        ports={ports}
        """
    )

    container = docker_client.containers.run(
        docker_image,
        command=command,
        name=container_name,
        detach=True,
        environment=env,
        privileged=True,
        volumes=volumes,
        network=DOCKER_STARCRAFT_NETWORK,
        ports=ports
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
    for container in docker_client.containers.list(filters={"name": name_filter}):
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

    # todo: this is a quick fix, do it properly later
    existing_files = itertools.chain(
        find_logs(launch_params["log_dir"], launch_params["game_name"]),
        find_replays(launch_params["map_dir"], launch_params["game_name"]),
        find_results(launch_params["log_dir"], launch_params["game_name"]),
        find_frames(launch_params["log_dir"], launch_params["game_name"])
    )
    for file_ in existing_files:
        logger.debug(f"removing existing file {file_}")
        os.remove(file_)

    for nth_player, player in enumerate(players):
        launch_image(player, nth_player=nth_player, num_players=len(players), **launch_params)

    logger.debug("checking if game has launched properly...")
    time.sleep(1)
    start_containers = running_containers(launch_params["game_name"])
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

    logger.info(f"waiting until game {launch_params['game_name']} is finished...")
    running_time = time.time()
    while True:
        containers = running_containers(launch_params["game_name"])
        if len(containers) == 0:  # game finished
            break
        if len(containers) >= 2:  # update the last time when there were multiple containers
            running_time = time.time()
        if len(containers) == 1 and time.time() - running_time > MAX_TIME_RUNNING_SINGLE_CONTAINER:
            raise ContainerException(
                f"""
                One lingering container has been found after single container timeout
                ({MAX_TIME_RUNNING_SINGLE_CONTAINER} sec), the game probably crashed.
                """
            )
        logger.debug(f"waiting. {containers}")
        wait_callback()

    exit_codes = [container_exit_code(container) for container in containers]
    # remove containers before throwing exception
    logger.debug("removing game containers")
    remove_game_containers(launch_params["game_name"])

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
                    f"{player.write_dir}/{launch_params['game_name']}_{nth_player}",
                    player.read_dir
                )
