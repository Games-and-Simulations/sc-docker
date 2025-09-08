from setuptools._distutils import dir_util
from setuptools._distutils import errors as distutils_errors
import logging
import os
import re
import time
import platform
import subprocess
import shutil
from typing import Optional, List
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

def get_container_runtime():
    """
    Detect and return the appropriate container runtime client using explicit sockets only.

    Environment contract:
    - SCBW_RUNTIME_DOCKER_ROOT: unix:///var/run/docker.sock if present
    - SCBW_RUNTIME_PODMAN_ROOT: unix:///run/podman/podman.sock if present
    - SCBW_RUNTIME_PODMAN_USER: unix://$XDG_RUNTIME_DIR/podman/podman.sock if present

    Selection order when SCBW_CONTAINER_RUNTIME is NOT set:
      docker-root -> podman-user -> podman-root

    Override: Users can set SCBW_CONTAINER_RUNTIME to any of:
      - the value of one of the runtime variables (recommended):
          SCBW_CONTAINER_RUNTIME=$SCBW_RUNTIME_DOCKER_ROOT
      - the name of one of the runtime variables:
          SCBW_CONTAINER_RUNTIME=SCBW_RUNTIME_PODMAN_USER
      - a friendly label: docker-root | podman-user | podman-root
      - a direct socket URL (unix:///path) or filesystem path (/path/to.sock)
    """
    # Define env var names
    ENV_DOCKER_ROOT = "SCBW_RUNTIME_DOCKER_ROOT"
    ENV_PODMAN_ROOT = "SCBW_RUNTIME_PODMAN_ROOT"
    ENV_PODMAN_USER = "SCBW_RUNTIME_PODMAN_USER"

    def _url_for_socket(path: str) -> str:
        return path if path.startswith("unix://") or path.startswith("tcp://") else f"unix://{path}"

    def _ping_client(url: str):
        client = docker.DockerClient(base_url=url)
        client.ping()
        return client

    # Discover sockets
    xdg_runtime = os.environ.get('XDG_RUNTIME_DIR', f"/run/user/{os.getuid() if hasattr(os, 'getuid') else 1000}")
    docker_root_sock = "/var/run/docker.sock"
    podman_root_sock = "/run/podman/podman.sock"
    podman_user_sock = f"{xdg_runtime}/podman/podman.sock"

    # Set or clear runtime env vars based on existence
    def _set_runtime_env(var_name: str, sock_path: str):
        if os.path.exists(sock_path):
            os.environ[var_name] = _url_for_socket(sock_path)
            return os.environ[var_name]
        else:
            # Do not leave stale values around
            if var_name in os.environ:
                os.environ.pop(var_name, None)
            return None

    runtime_urls = {
        'docker-root': _set_runtime_env(ENV_DOCKER_ROOT, docker_root_sock),
        'podman-root': _set_runtime_env(ENV_PODMAN_ROOT, podman_root_sock),
        'podman-user': _set_runtime_env(ENV_PODMAN_USER, podman_user_sock),
    }

    # Resolve requested selection
    requested = os.environ.get('SCBW_CONTAINER_RUNTIME', '').strip()

    def _resolve_requested(req: str) -> (str, str):
        """Return (label, url) or (None, None) if not resolvable."""
        if not req:
            return None, None
        # If it's a variable name, dereference it
        if req in (ENV_DOCKER_ROOT, ENV_PODMAN_ROOT, ENV_PODMAN_USER):
            url = os.environ.get(req)
            label_map = {
                ENV_DOCKER_ROOT: 'docker-root',
                ENV_PODMAN_ROOT: 'podman-root',
                ENV_PODMAN_USER: 'podman-user',
            }
            return label_map[req], url
        # Friendly labels
        if req in runtime_urls:
            return req, runtime_urls[req]
        # If it looks like a URL or a filesystem path
        if req.startswith('unix://') or req.startswith('tcp://'):
            # Best-effort label inference
            label = 'docker-root' if '/docker.sock' in req else ('podman-user' if '/podman/podman.sock' in req and xdg_runtime in req else ('podman-root' if '/podman/podman.sock' in req else 'custom'))
            return label, req
        if req.startswith('/'):
            if os.path.exists(req):
                return ('docker-root' if '/docker.sock' in req else ('podman-user' if '/podman/podman.sock' in req and xdg_runtime in req else ('podman-root' if '/podman/podman.sock' in req else 'custom')),
                        _url_for_socket(req))
            else:
                return None, None
        # Otherwise, not recognized
        return None, None

    label, url = _resolve_requested(requested)
    if label and url:
        try:
            client = _ping_client(url)
            logger.info(f"Using container runtime (from SCBW_CONTAINER_RUNTIME): {label} -> {url}")
            return client, label
        except Exception as e:
            raise RuntimeError(f"SCBW_CONTAINER_RUNTIME is set but not usable: {requested}. Error: {e}")

    if requested:
        # Requested but could not resolve
        raise RuntimeError(f"SCBW_CONTAINER_RUNTIME='{requested}' is not recognized.\n"
                           f"Use one of: {ENV_DOCKER_ROOT}, {ENV_PODMAN_USER}, {ENV_PODMAN_ROOT},\n"
                           f"labels: docker-root | podman-user | podman-root,\n"
                           f"or a direct socket URL/path.")

    # AUTO: try in preferred order with ping
    for auto_label in ('podman-user', 'podman-root', 'docker-root'):
        url = runtime_urls.get(auto_label)
        if not url:
            continue
        try:
            client = _ping_client(url)
            os.environ['SCBW_CONTAINER_RUNTIME'] = url
            logger.info(f"Using container runtime: {auto_label} -> {url}")
            return client, auto_label
        except Exception as e:
            logger.debug(f"Runtime candidate {auto_label} not usable: {e}")

    raise RuntimeError("No usable container runtime found. Tried podman-user, docker-root, podman-root.")

# Initialize the container runtime
try:
    docker_client, container_runtime = get_container_runtime()
    logger.info(f"Container runtime initialized: {container_runtime}")
except Exception as e:
    logger.error(f"Failed to initialize container runtime: {e}")
    # No fallback to docker.from_env(); explicit sockets only
    raise

DOCKER_STARCRAFT_NETWORK = "sc_net"
SUBNET_CIDR = "**********/16"
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
    # docker_client.containers.run("hello-world")
    logger.debug(f"using docker API version {version}")


def ensure_local_net(
        network_name: str = DOCKER_STARCRAFT_NETWORK,
        subnet_cidr: str = SUBNET_CIDR
) -> None:
    """
    Create docker local net if not found.
    Uses simple bridge network without isolation to allow host communication.

    :raises docker.errors.APIError
    """
    logger.info(f"checking whether docker has network {network_name}")
    networks = docker_client.networks.list(names=DOCKER_STARCRAFT_NETWORK)
    output = networks[0].short_id if networks else None
    if not output:
        logger.info("network not found, creating non-isolated bridge network...")
        # Create bridge network with isolation disabled to allow host communication
        output = docker_client.networks.create(
            DOCKER_STARCRAFT_NETWORK, 
            driver="bridge",
            options={"isolate": "true"}
        ).short_id
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
        mem_limit: Optional[str],
        
        # debug options
        debug: bool = False,
        debug_log_dir: Optional[str] = None
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
    
    # Fix permissions for Podman compatibility
    # Note: chmod has no effect on Windows but is harmless
    try:
        os.chmod(log_dir, 0o777)
        os.chmod(crashes_dir, 0o777)
    except (OSError, NotImplementedError):
        pass  # Windows may not support chmod on mounted volumes
    
    # Switch to debug image if debug mode is enabled
    if debug:
        docker_image = docker_image.replace(":game", ":dbg")
        logger.info(f"Debug mode enabled, using debug image: {docker_image}")

    volumes = {
        xoscmounts(log_dir): {"bind": LOG_DIR, "mode": "rw"},
        xoscmounts(map_dir): {"bind": MAP_DIR, "mode": "rw"},
        xoscmounts(crashes_dir): {"bind": ERRORS_DIR, "mode": "rw"},
        xoscmounts(bwapi_data_bwta_dir): {"bind": BWAPI_DATA_BWTA_DIR, "mode": "rw"},
        xoscmounts(bwapi_data_bwta2_dir): {"bind": BWAPI_DATA_BWTA2_DIR, "mode": "rw"},
    }
    
    # Mount debug log directory if specified
    if debug and debug_log_dir:
        debug_container_dir = "/debug_logs"
        # Expand tilde and create debug subdirectory
        expanded_debug_dir = os.path.expanduser(debug_log_dir)
        debug_subdir = os.path.join(expanded_debug_dir, "debug")
        os.makedirs(debug_subdir, mode=0o777, exist_ok=True)
        try:
            os.chmod(debug_subdir, 0o777)
        except (OSError, NotImplementedError):
            pass
        volumes[xoscmounts(debug_subdir)] = {"bind": debug_container_dir, "mode": "rw"}
        logger.debug(f"Platform: {platform.system()}, Debug mount: {debug_subdir} -> {debug_container_dir}")
        logger.info(f"Debug logs will be saved to: {debug_subdir}")

    ports = {}
    if not headless:
        ports.update({"5900/tcp": vnc_base_port + nth_player})
    
    # No port mapping for StarCraft ports - containers communicate directly via custom network

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
    
    # Always set BWAPI_AUTO_MENU with appropriate defaults to avoid unbound variable error
    if isinstance(player, HumanPlayer) and "BWAPI_AUTO_MENU_HUMAN" in os.environ:
        # Human-specific auto_menu override (--manual flag)
        env["BWAPI_AUTO_MENU"] = os.environ["BWAPI_AUTO_MENU_HUMAN"]
    elif "BWAPI_AUTO_MENU" in os.environ:
        # Global auto_menu setting for all players
        env["BWAPI_AUTO_MENU"] = os.environ["BWAPI_AUTO_MENU"]
    else:
        # Default values: LAN for bots, LAN for humans (unless overridden above)
        env["BWAPI_AUTO_MENU"] = "LAN"
    
    # Always set BWAPI_LAN_MODE with proper default for LAN multiplayer
    env["BWAPI_LAN_MODE"] = os.environ.get("BWAPI_LAN_MODE", "Local Area Network (UDP)")
    
    # Debug containers start normally by default - no automatic debugging
    # All debugging tools are available via manual docker exec commands
    # See DEBUG.md for usage instructions

    if isinstance(player, BotPlayer):
        # Only mount write directory, read and AI
        # are copied from the bot directory in proper places in bwapi-data
        bot_data_write_dir = f"{game_dir}/{game_name}/write_{nth_player}/"
        os.makedirs(bot_data_write_dir, mode=0o777, exist_ok=True)  # todo: proper mode
        # Fix permissions for Podman compatibility
        try:
            os.chmod(bot_data_write_dir, 0o777)
        except (OSError, NotImplementedError):
            pass
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

    run_opts = {
        "nano_cpus": nano_cpus,
        "mem_limit": mem_limit or None
    }
    """
    ;run_opts['privileged'] = True
    ;logger.info("Adding privileged for networking")
    ;if debug:
    ;    # Add capabilities for debugging (e.g., strace, tcpdump)
    ;    run_opts['security_opt'] = ['seccomp=unconfined']
    ;    run_opts['privileged'] = True
    ;    logger.info("Adding privileged for debugging")
    ;else:
    ;    logger.info("Not adding capabilities for networking or debuging")
    """
    # Launch container using the standard Docker client
    network_config = DOCKER_STARCRAFT_NETWORK
    
    logger.debug(
        "\n"
        f"docker_image={docker_image}\n"
        f"command={pformat(command, indent=4)}\n"
        f"name={container_name}\n"
        f"detach={True}\n"
        f"environment={pformat(env, indent=4)}\n"
        f"volumes={pformat(volumes, indent=4)}\n"
        f"network={network_config}\n"
        f"ports={ports}\n"
        f"run_opts={pformat(run_opts, indent=4)}\n"
    )

    container = docker_client.containers.run(
        docker_image,
        command=command,
        name=container_name,
        detach=True,
        environment=env,
        volumes=volumes,
        network=network_config,  # Use custom sc_net for container communication
        ports=ports,
        **run_opts
    )
    if container:
        container_id = running_containers(container_name)
        logger.info(f"launched {player}")
        logger.debug(f"container name = '{container_name}', container id = '{container_id[0] if container_id else 'unknown'}'")
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
    
    try:
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
        
        # Print container logs if any container failed
        if any(exit_code != 0 for exit_code in exit_codes):
            logger.error("One or more containers failed. Container logs:")
            for container in containers:
                logger.error(f"Logs for container {container.name}:")
                try:
                    logs = container.logs().decode('utf-8')
                    logger.error(logs)
                except Exception as e:
                    logger.error(f"Failed to get logs for container {container.name}: {e}")

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
                    dir_util.copy_tree(
                        f"{game_dir}/{game_name}/write_{nth_player}",
                        player.read_dir
                    )
    except Exception as e:
        # Clean up containers on any error
        logger.debug("removing game containers due to error")
        remove_game_containers(game_name)
        raise
