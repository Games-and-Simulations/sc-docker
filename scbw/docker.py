import logging
import os
import re
import subprocess
import sys
import time
from distutils.dir_util import copy_tree
from os.path import exists, abspath, dirname
from typing import List, Optional, Callable, Dict, Any

from .defaults import *
from .error import DockerException, GameException, RealtimeOutedException, ContainerException
from .game_type import GameType
from .player import BotPlayer, Player, HumanPlayer
from .utils import download_file
from .vnc import launch_vnc_viewer
logger = logging.getLogger(__name__)

DOCKER_STARCRAFT_NETWORK = "sc_net"
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

try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, 'wb')


def check_docker_version():
    logger.info('checking docker version')
    try:
        out = subprocess.check_output(
            ['docker', 'version', '--format', "'{{.Server.APIVersion}}'"])
    except Exception:
        raise DockerException(
            'An error occurred while trying to call `docker version`, did you install docker?'
        )
    logger.debug(('Using docker API version %s' % (out, )))


def check_docker_can_run():
    logger.info('checking docker can run')
    try:
        out = subprocess.check_output(['docker', 'run', 'hello-world'])
    except Exception:
        raise DockerException(
            'An error occurred while trying to call `docker run hello-world`, do you have sufficient rights to run sudo?'
        )
    if (b'Hello' not in out):
        raise DockerException((
            "Docker did not run properly - could'nt find 'Hello' in hello-world run, found %s"
            % (out, )))


def check_docker_has_local_net():
    logger.info(
        ('checking docker has network %s' % (DOCKER_STARCRAFT_NETWORK, )))
    try:
        out = subprocess.check_output([
            'docker', 'network', 'ls', '-f',
            ('name=%s' % (DOCKER_STARCRAFT_NETWORK, )), '-q'
        ])
    except Exception:
        raise DockerException((
            'An error occurred while trying to call `docker network ls -f name=%s -q`'
            % (DOCKER_STARCRAFT_NETWORK, )))
    logger.debug(('docker network id: %s' % (out, )))
    return bool(out)


def create_local_net():
    try:
        logger.info(
            ('creating docker local net %s' % (DOCKER_STARCRAFT_NETWORK, )))
        out = subprocess.check_output([
            'docker', 'network', 'create', '--subnet=172.18.0.0/16',
            DOCKER_STARCRAFT_NETWORK
        ])
    except Exception:
        raise DockerException((
            'An error occurred while trying to call `docker network create --subnet=172.18.0.0/16 %s`'
            % (DOCKER_STARCRAFT_NETWORK, )))
    logger.debug(('docker network id: %s' % (out, )))


def check_docker_has_local_image(image):
    try:
        logger.info(('checking if there is local image %s' % (image, )))
        out = subprocess.check_output(['docker', 'images', '-q', image])
    except Exception:
        raise DockerException(
            ('An error occurred while trying to call `docker images -q %s`' %
             (image, )))
    logger.debug(('docker image id: %s' % (out, )))
    return bool(out)


def create_local_image(image):
    try:
        pkg_docker_dir = ('%s/local_docker' % (abspath(dirname(__file__)), ))
        base_dir = (SCBW_BASE_DIR + '/docker')
        logger.info(('creating docker local image' % ()))
        logger.info(('copying files from %s to %s' % (pkg_docker_dir,
                                                      base_dir)))
        copy_tree(pkg_docker_dir, base_dir)
        logger.info(('pulling image %s, this may take a while...' %
                     (SC_PARENT_IMAGE, )))
        if (subprocess.call(
            ['docker', 'pull', SC_PARENT_IMAGE], stdout=sys.stderr.buffer) !=
                0):
            raise DockerException(
                f"an error occurred while calling `docker pull {SC_PARENT_IMAGE}`")
        if subprocess.call(['docker', 'tag', SC_PARENT_IMAGE, SC_JAVA_IMAGE],
                           stdout=sys.stderr.buffer) != 0:
            raise DockerException(
                ('an error occurred while calling `docker tag %s %s`' %
                 (SC_PARENT_IMAGE, SC_JAVA_IMAGE)))
        starcraft_zip_file = ('%s/starcraft.zip' % (base_dir, ))
        if (not exists(starcraft_zip_file)):
            logger.info(
                ('downloading starcraft.zip to %s' % (starcraft_zip_file, )))
            download_file('http://files.theabyss.ru/sc/starcraft.zip',
                          starcraft_zip_file)
        logger.info(
            ('building local image %s, this may take a while...' % (image, )))
        if (subprocess.call(
            ['docker', 'build', '-f', 'game.dockerfile', '-t', image, '.'],
                cwd=base_dir,
                stdout=sys.stderr.buffer) != 0):
            raise DockerException()
        logger.info(('successfully built image %s' % (image, )))
    except Exception:
        raise DockerException(
            ('An error occurred while trying to build local image' % ()))


def remove_game_image(image_name):
    has_image = check_output(
        ('docker images %s -q' % (image_name, )), shell=True)
    if has_image:
        call(('docker rmi --force %s' % (image_name, )), shell=True)


def check_dockermachine() -> bool:
    """
    Checks that docker-machine is available on the computer
    """
    logger.debug("checking docker-machine presence")
    try:
        out = subprocess.check_output(['docker-machine', 'version'])
        out = out.decode("utf-8")
        out = out.replace('docker-machine.exe', '').replace('docker-machine', '')
        out = out.strip()
        logger.debug(f"Using docker machine version {out}")
        return True
    except Exception as e:
        logger.debug(f"Docker machine not present")
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

    try:
        out = subprocess.check_output(['docker-machine', 'ip'])
        return out.decode("utf-8").strip()
    except Exception as e:
        logger.debug(f"Docker machine not present")
        return None


def check_output(*args, **kwargs):
    try:
        return subprocess.check_output(*args, **kwargs)
    except subprocess.CalledProcessError:
        print(('Failed calling %s %s' % (args, kwargs)))
        sys.exit(1)


def call(*args, **kwargs):
    code = subprocess.call(*args, **kwargs)
    if (code != 0):
        print(('Failed calling %s %s' % (args, kwargs)))
        sys.exit(1)


def check_docker_requirements(image):
    check_docker_version()
    check_docker_can_run()
    (check_docker_has_local_net() or create_local_net())
    (check_docker_has_local_image(image) or create_local_image(image))


def xoscmounts(host_mount):
    """
    Cross OS compatible mount dirs
    """
    callback_lower_drive_letter = (lambda pat: pat.group(1).lower())
    host_mount = re.sub('^([a-zA-Z])\\:', callback_lower_drive_letter,
                        host_mount)
    host_mount = re.sub('^([a-z])', '//\\1', host_mount)
    host_mount = re.sub('\\\\', '/', host_mount)
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
        docker_opts: List[str]):
    #

    container_name = f"{game_name}_{nth_player}_{player.name.replace(' ', '_')}"

    cmd = ["docker", "run",

           "-d",
           "--privileged",

           "--name", container_name,

           "--volume", f"{xoscmounts(log_dir)}:{LOG_DIR}:rw",
           "--volume", f"{xoscmounts(map_dir)}:{MAP_DIR}:rw",
           "--volume", f"{xoscmounts(bwapi_data_bwta_dir)}:{BWAPI_DATA_BWTA_DIR}:rw",
           "--volume", f"{xoscmounts(bwapi_data_bwta2_dir)}:{BWAPI_DATA_BWTA2_DIR}:rw",
           ]

    if docker_opts:
        cmd += docker_opts
    if ('--net' not in docker_opts):
        cmd += ['--net', DOCKER_STARCRAFT_NETWORK]
    if (not headless):
        cmd += ['-p', ('%s:5900' % ((vnc_base_port + nth_player), ))]
    if isinstance(player, BotPlayer):
        # Only mount write directory, read and AI
        # are copied from the bot directory in proper places in bwapi-data
        bot_data_write_dir = f"{player.bot_dir}/write/{game_name}_{nth_player}"
        os.makedirs(bot_data_write_dir, mode=0o777, exist_ok=True)  # todo: proper mode
        cmd += ["--volume", f"{xoscmounts(bot_data_write_dir)}:{BOT_DATA_WRITE_DIR}:rw"]
        cmd += ["--volume", f"{xoscmounts(player.bot_dir)}:{BOT_DIR}:ro"]

        if player.meta.javaDebugPort is not None:
            cmd += ["-p", f"{player.meta.javaDebugPort}:{player.meta.javaDebugPort}"]

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

        TM_LOG_RESULTS=f"../logs/{game_name}_{nth_player}_results.json",
        TM_LOG_FRAMETIMES=f"../logs/{game_name}_{nth_player}_frames.csv",
        TM_SPEED_OVERRIDE=game_speed,
        TM_ALLOW_USER_INPUT="1" if isinstance(player, HumanPlayer) else "0",

        EXIT_CODE_REALTIME_OUTED=EXIT_CODE_REALTIME_OUTED,

        JAVA_DEBUG="0"
    )
    if isinstance(player, BotPlayer):
        env['BOT_FILE'] = player.bot_basefilename
        env['BOT_BWAPI'] = player.bwapi_version
        if player.meta.javaDebugPort is not None:
            env['JAVA_DEBUG'] = "1"
            env['JAVA_DEBUG_PORT'] = player.meta.javaDebugPort

    if timeout is not None:
        env["PLAY_TIMEOUT"] = timeout

    for key, value in env.items():
        cmd += ["-e", f"{key}={value}"]

    cmd += [docker_image]
    if isinstance(player, BotPlayer):
        cmd += ['/app/play_bot.sh']
    else:
        cmd += ['/app/play_human.sh']
    entrypoint_opts = []
    is_server = (nth_player == 0)
    if (not headless):
        entrypoint_opts += ['--headful']
    else:
        entrypoint_opts += [
            '--game', game_name, '--name', player.name, '--race',
            player.race.value, '--lan'
        ]
        if is_server:
            entrypoint_opts += [
                '--host', '--map', ('/app/sc/maps/%s' % (map_name, ))
            ]
        else:
            entrypoint_opts += ['--join']
    cmd += entrypoint_opts

    logger.debug(" ".join(f"'{s}'" for s in cmd))
    code = subprocess.call(cmd, stdout=DEVNULL)

    if code == 0:
        container_id = subprocess \
            .check_output(["docker", "ps", "-f", f"name={container_name}", "-q"]) \
            .decode("utf-8").strip("'\"\n")
        logger.info(f"launched {player}")
        logger.debug(f"container name '{container_name}'")
        logger.debug(f"container id '{container_id}'")
    else:
        raise DockerException(
            f"could not launch {player} in container {container_name}")


def running_containers(name_filter):
    out = subprocess.check_output(f'docker ps -f "name={name_filter}" -q', shell=True)
    containers = [container.strip()
                  for container in out.decode("utf-8").split("\n")
                  if container != ""]
    return containers


def stop_containers(containers: List[str]):
    if len(containers):
        subprocess.call(['docker', 'stop'] + containers, stdout=sys.stderr.buffer)


def cleanup_containers(containers: List[str]):
    if len(containers):
        subprocess.call(['docker', 'rm'] + containers, stdout=DEVNULL)


def container_exit_code(container: str) -> int:
    out = subprocess.check_output(['docker', 'inspect', container,
                                   "--format='{{.State.ExitCode}}'"])
    return int(out.decode("utf-8").strip("\n\r\t '\""))


def launch_game(players: List[Player], launch_params: Dict[str, Any],
                show_all: bool, read_overwrite: bool,
                wait_callback: Callable):
    """
    :raises DockerException, ContainerException, RealtimeOutedException
    """
    #
    if len(players) == 0:
        raise GameException("At least one player must be specified")

    for i, player in enumerate(players):
        launch_image(player, nth_player=i, num_players=len(players), **launch_params)

    logger.debug("Checking if game has launched properly...")
    time.sleep(1)
    start_containers = running_containers(launch_params['game_name'])
    if len(start_containers) != len(players):
        raise DockerException("Some containers exited prematurely, please check logs")

    if not launch_params['headless']:
        for i, player in enumerate(players if show_all else players[:1]):
            port = launch_params['vnc_base_port'] + i
            host = launch_params['vnc_host']
            logger.info(f"Launching vnc viewer for {player} on address {host}:{port}")
            launch_vnc_viewer(host, port)

        logger.info("\n"
                    "In headful mode, you must specify and start the game manually.\n"
                    "Select the map, wait for bots to join the game "
                    "and then start the game.")

    logger.info(f"Waiting until game {launch_params['game_name']} is finished...")
    while True:
        containers = running_containers(launch_params['game_name'])
        if len(containers) == 0:
            break

        logger.debug(f"Waiting. {containers}")
        wait_callback()

    exit_codes = [container_exit_code(container) for container in containers]

    # remove containers before throwing exception
    logger.debug("Removing game containers")
    cleanup_containers(start_containers)

    if any(exit_code == EXIT_CODE_REALTIME_OUTED for exit_code in exit_codes):
        raise RealtimeOutedException(f"Some of the game containers has realtime outed.")
    if any(exit_code == 1 for exit_code in exit_codes):
        raise ContainerException(f"Some of the game containers has finished with error exit code.")

    if read_overwrite:
        logger.info('Overwriting bot files')
        for (nth_player, player) in enumerate(players):
            if isinstance(player, BotPlayer):
                logger.debug(('Overwriting files for %s' % (player, )))
                copy_tree(('%s/%s_%s' %
                           (player.write_dir, launch_params['game_name'],
                            nth_player)), player.read_dir)
