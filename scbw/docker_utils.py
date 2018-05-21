import distutils.dir_util
import distutils.errors
import itertools
import logging
import os
import os.path
import re
import shutil
import subprocess
import time
from pprint import pformat
import docker
import docker.errors
import docker.types
from scbw.defaults import SCBW_BASE_DIR, SC_PARENT_IMAGE, SC_JAVA_IMAGE, SC_BINARY_LINK
from scbw.error import ContainerException, DockerException, GameException, RealtimeOutedException
from scbw.game_type import GameType
from scbw.logs import find_frames, find_logs, find_replays, find_scores
from scbw.player import BotPlayer, HumanPlayer, Player
from scbw.utils import download_file, random_string
from scbw.vnc import launch_vnc_viewer
logger = logging.getLogger(__name__)
logging.getLogger('urllib3.connectionpool').propagate = False
docker_client = docker.from_env()
DOCKER_STARCRAFT_NETWORK = 'sc_net'
SUBNET_CIDR = '172.18.0.0/16'
BASE_VNC_PORT = 5900
VNC_HOST = 'localhost'
APP_DIR = '/app'
LOG_DIR = ('%s/logs' % (APP_DIR, ))
SC_DIR = ('%s/sc' % (APP_DIR, ))
BWTA_DIR = ('%s/bwta' % (APP_DIR, ))
BWAPI_DIR = ('%s/bwapi' % (APP_DIR, ))
BOT_DIR = ('%s/bot' % (APP_DIR, ))
MAP_DIR = ('%s/maps' % (SC_DIR, ))
ERRORS_DIR = ('%s/Errors' % (SC_DIR, ))
BWAPI_DATA_DIR = ('%s/bwapi-data' % (SC_DIR, ))
BWAPI_DATA_BWTA_DIR = ('%s/BWTA' % (BWAPI_DATA_DIR, ))
BWAPI_DATA_BWTA2_DIR = ('%s/BWTA2' % (BWAPI_DATA_DIR, ))
BOT_DATA_SAVE_DIR = ('%s/save' % (BWAPI_DATA_DIR, ))
BOT_DATA_READ_DIR = ('%s/read' % (BWAPI_DATA_DIR, ))
BOT_DATA_WRITE_DIR = ('%s/write' % (BWAPI_DATA_DIR, ))
BOT_DATA_AI_DIR = ('%s/AI' % (BWAPI_DATA_DIR, ))
BOT_DATA_LOGS_DIR = ('%s/logs' % (BWAPI_DATA_DIR, ))
EXIT_CODE_REALTIME_OUTED = 2
MAX_TIME_RUNNING_SINGLE_CONTAINER = 20
try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull, 'wb')


def ensure_docker_can_run():
    """
    :raises docker.errors.ContainerError
    :raises docker.errors.ImageNotFound
    :raises docker.errors.APIError
    """
    logger.info('checking docker can run')
    version = docker_client.version()['ApiVersion']
    docker_client.containers.run('hello-world')
    logger.debug(('using docker API version %s' % (version, )))


def ensure_local_net(network_name=DOCKER_STARCRAFT_NETWORK,
                     subnet_cidr=SUBNET_CIDR):
    """
    Create docker local net if not found.

    :raises docker.errors.APIError
    """
    logger.info(('checking whether docker has network %s' % (network_name, )))
    ipam_pool = docker.types.IPAMPool(subnet=subnet_cidr)
    ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
    networks = docker_client.networks.list(names=DOCKER_STARCRAFT_NETWORK)
    output = (networks[0].short_id if networks else None)
    if (not output):
        logger.info('network not found, creating ...')
        output = docker_client.networks.create(
            DOCKER_STARCRAFT_NETWORK, ipam=ipam_config).short_id
    logger.debug(('docker network id: %s' % (output, )))


def ensure_local_image(local_image,
                       parent_image=SC_PARENT_IMAGE,
                       java_image=SC_JAVA_IMAGE,
                       starcraft_base_dir=SCBW_BASE_DIR,
                       starcraft_binary_link=SC_BINARY_LINK):
    """
    Check if `local_image` is present locally. If it is not, pull parent images and build.
    This includes pulling starcraft binary.

    :raises docker.errors.ImageNotFound
    :raises docker.errors.APIError
    """
    logger.info(('checking if there is local image %s' % (local_image, )))
    docker_images = docker_client.images.list(local_image)
    if (len(docker_images) and (docker_images[0].short_id is not None)):
        logger.info(('image %s found locally.' % (local_image, )))
        return
    logger.info('image not found locally, creating...')
    pkg_docker_dir = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 'local_docker')
    base_dir = os.path.join(starcraft_base_dir, 'docker')
    logger.info(('copying files from %s to %s.' % (pkg_docker_dir, base_dir)))
    distutils.dir_util.copy_tree(pkg_docker_dir, base_dir)
    starcraft_zip_file = ('%s/starcraft.zip' % (base_dir, ))
    if (not os.path.exists(starcraft_zip_file)):
        logger.info(
            ('downloading starcraft.zip to %s' % (starcraft_zip_file, )))
        download_file(starcraft_binary_link, starcraft_zip_file)
    logger.info(
        ('pulling image %s, this may take a while...' % (parent_image, )))
    pulled_image = docker_client.images.pull(parent_image)
    pulled_image.tag(java_image)
    logger.info(('building local image %s, this may take a while...' %
                 (local_image, )))
    docker_client.images.build(
        path=base_dir, dockerfile='game.dockerfile', tag=local_image)
    logger.info(('successfully built image %s' % (local_image, )))


def remove_game_image(image_name):
    try:
        docker_client.images.get(image_name)
    except docker.errors.ImageNotFound:
        pass
    except docker.errors.APIError:
        logger.error(('there occurred an error trying to find image %s' %
                      (image_name, )))
    else:
        docker_client.images.remove(image_name, force=True)
    logger.info(('docker image %s removed.' % (image_name, )))


def check_dockermachine():
    """
    Checks that docker-machine is available on the computer

    :raises FileNotFoundError if docker-machine is not present
    """
    logger.debug('checking docker-machine presence')
    try:
        out = subprocess.check_output(['docker-machine',
                                       'version']).decode('utf-8').replace(
                                           'docker-machine.exe', '').replace(
                                               'docker-machine', '').strip()
        logger.debug(('using docker machine version %s' % (out, )))
        return True
    except Exception:
        logger.debug(('docker machine not present' % ()))
        return False


def dockermachine_ip():
    """
    Gets IP address of the default docker machine
    Returns None if no docker-machine executable
    in the PATH and if there no Docker machine
    with name default present
    """
    if (not check_dockermachine()):
        return None
    try:
        out = subprocess.check_output(['docker-machine', 'ip'])
        return out.decode('utf-8').strip()
    except Exception:
        logger.debug(('docker machine not present' % ()))
        return None


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


def launch_image(player, nth_player, num_players, headless, game_name,
                 map_name, game_type, game_speed, timeout, hide_names,
                 random_names, drop_players, allow_input, auto_launch,
                 game_dir, bot_dir, map_dir, bwapi_data_bwta_dir,
                 bwapi_data_bwta2_dir, vnc_base_port, vnc_host,
                 capture_movement, docker_image, docker_opts):
    """
    :raises docker,errors.APIError
    :raises DockerException
    """
    container_name = ('%s_%s_%s' % (game_name, nth_player,
                                    player.name.replace(' ', '_')))
    log_dir = ('%s/%s/logs_%s' % (game_dir, game_name, nth_player))
    crashes_dir = ('%s/%s/crashes_%s' % (game_dir, game_name, nth_player))
    os.makedirs(log_dir, mode=511, exist_ok=True)
    os.makedirs(crashes_dir, mode=511, exist_ok=True)
    volumes = {
        xoscmounts(log_dir): {
            'bind': LOG_DIR,
            'mode': 'rw'
        },
        xoscmounts(map_dir): {
            'bind': MAP_DIR,
            'mode': 'rw'
        },
        xoscmounts(crashes_dir): {
            'bind': ERRORS_DIR,
            'mode': 'rw'
        },
        xoscmounts(bwapi_data_bwta_dir): {
            'bind': BWAPI_DATA_BWTA_DIR,
            'mode': 'rw'
        },
        xoscmounts(bwapi_data_bwta2_dir): {
            'bind': BWAPI_DATA_BWTA2_DIR,
            'mode': 'rw'
        }
    }
    ports = {}
    if (not headless):
        ports.update({'5900/tcp': (vnc_base_port + nth_player)})
    env = dict(
        PLAYER_NAME=(player.name if (not random_names) else random_string(8)),
        PLAYER_RACE=player.race.value,
        NTH_PLAYER=nth_player,
        NUM_PLAYERS=num_players,
        GAME_NAME=game_name,
        MAP_NAME=('/app/sc/maps/%s' % (map_name, )),
        GAME_TYPE=game_type.value,
        SPEED_OVERRIDE=game_speed,
        HIDE_NAMES=('1' if hide_names else '0'),
        DROP_PLAYERS=('1' if drop_players else '0'),
        TM_LOG_RESULTS=('../logs/scores.json' % ()),
        TM_LOG_FRAMETIMES=('../logs/frames.csv' % ()),
        TM_SPEED_OVERRIDE=game_speed,
        TM_ALLOW_USER_INPUT=('1' if (isinstance(player, HumanPlayer) or
                                     allow_input) else '0'),
        EXIT_CODE_REALTIME_OUTED=EXIT_CODE_REALTIME_OUTED,
        CAPTURE_MOUSE_MOVEMENT=('1' if capture_movement else '0'),
        HEADFUL_AUTO_LAUNCH=('1' if auto_launch else '0'),
        JAVA_DEBUG='0')
    if (timeout is not None):
        env['PLAY_TIMEOUT'] = timeout
    if isinstance(player, BotPlayer):
        bot_data_write_dir = ('%s/%s/write_%s/' % (game_dir, game_name,
                                                   nth_player))
        os.makedirs(bot_data_write_dir, mode=511, exist_ok=True)
        volumes.update({
            xoscmounts(bot_data_write_dir): {
                'bind': BOT_DATA_WRITE_DIR,
                'mode': 'rw'
            },
            xoscmounts(player.bot_dir): {
                'bind': BOT_DIR,
                'mode': 'ro'
            }
        })
        env['BOT_FILE'] = player.bot_basefilename
        env['BOT_BWAPI'] = player.bwapi_version
        command = ['/app/play_bot.sh']
        if (player.meta.javaDebugPort is not None):
            ports.update({
                'player.meta.javaDebugPort/tcp':
                player.meta.javaDebugPort
            })
            env['JAVA_DEBUG'] = '1'
            env['JAVA_DEBUG_PORT'] = player.meta.javaDebugPort
        if (player.meta.javaOpts is not None):
            env['JAVA_OPTS'] = player.meta.javaOpts
    else:
        command = ['/app/play_human.sh']
    is_server = (nth_player == 0)
    entrypoint_opts = ['--headful']
    if headless:
        entrypoint_opts = [
            '--game', game_name, '--name', player.name, '--race',
            player.race.value, '--lan'
        ]
        if is_server:
            entrypoint_opts += [
                '--host', '--map', ('/app/sc/maps/%s' % (map_name, ))
            ]
        else:
            entrypoint_opts += ['--join']
    command += entrypoint_opts
    logger.debug(("""
docker_image=%s
command=%s
name=%s
detach=%s
environment=%s
privileged=%s
volumes=%s
network=%s
ports=%s
""" % (docker_image, pformat(command, indent=4), container_name, True,
       pformat(env, indent=4), True, pformat(volumes, indent=4),
       DOCKER_STARCRAFT_NETWORK, ports)))
    container = docker_client.containers.run(
        docker_image,
        command=command,
        name=container_name,
        detach=True,
        environment=env,
        privileged=True,
        volumes=volumes,
        network=DOCKER_STARCRAFT_NETWORK,
        ports=ports)
    if container:
        container_id = running_containers(container_name)
        logger.info(('launched %s' % (player, )))
        logger.debug(("container name = '%s', container id = '%s'" %
                      (container_name, container_id)))
    else:
        raise DockerException(
            ('could not launch %s in container %s' % (player, container_name)))


def running_containers(name_filter):
    """
    :raises docker.exceptions.APIError
    """
    return [
        container.short_id
        for container in docker_client.containers.list(filters=
                                                       {'name': name_filter})
    ]


def remove_game_containers(name_filter):
    """
    :raises docker.exceptions.APIError
    """
    for container in docker_client.containers.list(
            filters={'name': name_filter}, all=True):
        container.stop()
        container.remove()


def container_exit_code(container_id):
    """
    :raises docker.errors.NotFound
    :raises docker.errors.APIError
    """
    container = docker_client.containers.get(container_id)
    return container.wait()['StatusCode']


def launch_game(players, launch_params, show_all, read_overwrite,
                wait_callback):
    """
    :raises DockerException, ContainerException, RealtimeOutedException
    """
    if (not players):
        raise GameException('at least one player must be specified')
    game_dir = launch_params['game_dir']
    game_name = launch_params['game_name']
    if os.path.exists(('%s/%s' % (game_dir, game_name))):
        logger.info(('removing existing game results of %s' % (game_name, )))
        shutil.rmtree(('%s/%s' % (game_dir, game_name)))
    for (nth_player, player) in enumerate(players):
        launch_image(
            player,
            nth_player=nth_player,
            num_players=len(players),
            **launch_params)
    logger.debug('checking if game has launched properly...')
    time.sleep(1)
    start_containers = running_containers(game_name)
    if (len(start_containers) != len(players)):
        raise DockerException(
            'some containers exited prematurely, please check logs')
    if (not launch_params['headless']):
        for (index, player) in enumerate((players
                                          if show_all else players[:1])):
            port = (launch_params['vnc_base_port'] + index)
            host = launch_params['vnc_host']
            logger.info(('launching vnc viewer for %s on address %s:%s' %
                         (player, host, port)))
            launch_vnc_viewer(host, port)
        logger.info("""
In headful mode, you must specify and start the game manually.
Select the map, wait for bots to join the game and then start the game.""")
    logger.info(('waiting until game %s is finished...' % (game_name, )))
    running_time = time.time()
    while True:
        containers = running_containers(game_name)
        if (len(containers) == 0):
            break
        if (len(containers) >= 2):
            running_time = time.time()
        if ((len(containers) == 1) and (
            (time.time() - running_time) > MAX_TIME_RUNNING_SINGLE_CONTAINER)):
            raise ContainerException((
                'One lingering container has been found after single container timeout (%s sec), the game probably crashed.'
                % (MAX_TIME_RUNNING_SINGLE_CONTAINER, )))
        logger.debug(('waiting. %s' % (containers, )))
        wait_callback()
    exit_codes = [container_exit_code(container) for container in containers]
    logger.debug('removing game containers')
    remove_game_containers(game_name)
    if any(((exit_code == EXIT_CODE_REALTIME_OUTED)
            for exit_code in exit_codes)):
        raise RealtimeOutedException(
            ('some of the game containers has realtime outed.' % ()))
    if any(((exit_code == 1) for exit_code in exit_codes)):
        raise ContainerException(
            ('some of the game containers has finished with error exit code.' %
             ()))
    if read_overwrite:
        logger.info('overwriting bot files')
        for (nth_player, player) in enumerate(players):
            if isinstance(player, BotPlayer):
                logger.debug(('overwriting files for %s' % (player, )))
                distutils.dir_util.copy_tree(
                    ('%s/%s/write_%s' % (game_dir, game_name,
                                         nth_player)), player.read_dir)
