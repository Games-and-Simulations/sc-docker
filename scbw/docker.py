import logging
import os
import re
import subprocess
import sys
import time
from distutils.dir_util import copy_tree
from os.path import exists, abspath, dirname
from .defaults import *
from .error import DockerException
from .game_type import GameType
from .player import BotPlayer, Player
from .utils import download_file
from .vnc import launch_vnc_viewer
logger = logging.getLogger(__name__)
DOCKER_STARCRAFT_NETWORK = 'sc_net'
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
                ('an error occurred while calling `docker pull %s`' %
                 (SC_PARENT_IMAGE, )))
        if (subprocess.call(
            ['docker', 'tag', SC_PARENT_IMAGE, SC_JAVA_IMAGE],
                stdout=sys.stderr.buffer) != 0):
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


BASE_VNC_PORT = 5900
APP_DIR = '/app'
LOG_DIR = ('%s/logs' % (APP_DIR, ))
SC_DIR = ('%s/sc' % (APP_DIR, ))
BWTA_DIR = ('%s/bwta' % (APP_DIR, ))
BWAPI_DIR = ('%s/bwapi' % (APP_DIR, ))
BOT_DIR = ('%s/bots' % (APP_DIR, ))
MAP_DIR = ('%s/maps' % (SC_DIR, ))
BWAPI_DATA_DIR = ('%s/bwapi-data' % (SC_DIR, ))
BWAPI_DATA_BWTA_DIR = ('%s/BWTA' % (BWAPI_DATA_DIR, ))
BWAPI_DATA_BWTA2_DIR = ('%s/BWTA2' % (BWAPI_DATA_DIR, ))
BOT_DATA_SAVE_DIR = ('%s/save' % (BWAPI_DATA_DIR, ))
BOT_DATA_READ_DIR = ('%s/read' % (BWAPI_DATA_DIR, ))
BOT_DATA_WRITE_DIR = ('%s/write' % (BWAPI_DATA_DIR, ))
BOT_DATA_AI_DIR = ('%s/AI' % (BWAPI_DATA_DIR, ))
BOT_DATA_LOGS_DIR = ('%s/logs' % (BWAPI_DATA_DIR, ))


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
                 map_name, game_type, game_speed, timeout, log_dir, bot_dir,
                 map_dir, bwapi_data_bwta_dir, bwapi_data_bwta2_dir,
                 vnc_base_port, docker_image, docker_opts):
    cmd = [
        'docker', 'run', '-d', '--rm', '--privileged', '--name', (
            '%s_%s_%s' % (game_name, nth_player,
                          player.name.replace(' ', '_'))), '--volume',
        ('%s:%s:rw' % (xoscmounts(log_dir), LOG_DIR)), '--volume', (
            '%s:%s:ro' % (xoscmounts(bot_dir), BOT_DIR)), '--volume', (
                '%s:%s:rw' % (xoscmounts(map_dir), MAP_DIR)), '--volume',
        ('%s:%s:rw' % (xoscmounts(bwapi_data_bwta_dir), BWAPI_DATA_BWTA_DIR)),
        '--volume', ('%s:%s:rw' % (xoscmounts(bwapi_data_bwta2_dir),
                                   BWAPI_DATA_BWTA2_DIR))
    ]
    if docker_opts:
        cmd += docker_opts
    if ('--net' not in docker_opts):
        cmd += ['--net', DOCKER_STARCRAFT_NETWORK]
    if (not headless):
        cmd += ['-p', ('%s:5900' % ((vnc_base_port + nth_player), ))]
    if isinstance(player, BotPlayer):
        bot_data_write_dir = ('%s/write/%s_%s' % (player.base_dir, game_name,
                                                  nth_player))
        os.makedirs(bot_data_write_dir, mode=511, exist_ok=True)
        cmd += [
            '--volume', ('%s:%s:rw' % (xoscmounts(bot_data_write_dir),
                                       BOT_DATA_WRITE_DIR))
        ]
    env = [
        '-e', ('PLAYER_NAME=%s' % (player.name, )), '-e', (
            'PLAYER_RACE=%s' % (player.race.value, )), '-e', (
                'NTH_PLAYER=%s' % (str(nth_player), )), '-e',
        ('NUM_PLAYERS=%s' % (str(num_players), )), '-e', ('GAME_NAME=%s' %
                                                          (game_name, )), '-e',
        ('MAP_NAME=/app/sc/maps/%s' % (map_name, )), '-e', (
            'GAME_TYPE=%s' % (game_type.value, )), '-e', ('SPEED_OVERRIDE=%s' %
                                                          (str(game_speed), ))
    ]
    if isinstance(player, BotPlayer):
        env += [
            '-e', ('BOT_NAME=%s' % (player.name, )), '-e',
            ('BOT_FILE=%s' % (player.bot_basefilename, ))
        ]
    if (timeout is not None):
        env += ['-e', ('PLAY_TIMEOUT=%s' % (timeout, ))]
    cmd += env
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
    logger.debug(cmd)
    code = subprocess.call(cmd, stdout=DEVNULL)
    if (code == 0):
        logger.info(('launched %s in container %s_%s_%s' %
                     (player, game_name, nth_player, player.name)))
    else:
        raise DockerException(('could not launch %s in container %s_%s_%s' %
                               (player, game_name, nth_player, player.name)))


def running_containers(name_prefix):
    out = subprocess.check_output(
        ('docker ps -f "name=%s" -q' % (name_prefix, )), shell=True)
    containers = [
        container.strip() for container in out.decode('utf-8').split("""
""") if (container != '')
    ]
    logger.debug(('running containers: %s' % (containers, )))
    return containers


def stop_containers(name_prefix):
    containers = running_containers(name_prefix)
    subprocess.call(
        (['docker', 'stop'] + containers), stdout=sys.stderr.buffer)


def launch_game(players,
                launch_params,
                show_all,
                read_overwrite,
                wait_callback=None):
    if (len(players) == 0):
        raise DockerException('At least one player must be specified')
    for (i, player) in enumerate(players):
        launch_image(
            player, nth_player=i, num_players=len(players), **launch_params)
    logger.info('Checking if game has launched properly...')
    time.sleep(2)
    containers = running_containers(launch_params['game_name'])
    if (len(containers) != len(players)):
        raise DockerException(
            'Some containers exited prematurely, please check logs')
    if (not launch_params['headless']):
        time.sleep(1)
        for (i, player) in enumerate((players if show_all else players[:1])):
            port = (launch_params['vnc_base_port'] + i)
            logger.info(('Launching vnc viewer for %s on port %s' % (player,
                                                                     port)))
            launch_vnc_viewer(port)
        logger.info("""
In headful mode, you must specify and start the game manually.
Select the map, wait for bots to join the game and then start the game.""")
    logger.info('Waiting until game is finished...')
    while (len(running_containers(launch_params['game_name'])) > 0):
        time.sleep(3)
        if (wait_callback is not None):
            wait_callback()
    if read_overwrite:
        logger.info('Overwriting bot files')
        for (nth_player, player) in enumerate(players):
            if isinstance(player, BotPlayer):
                logger.debug(('Overwriting files for %s' % (player, )))
                copy_tree(('%s/%s_%s' %
                           (player.write_dir, launch_params['game_name'],
                            nth_player)), player.read_dir)
