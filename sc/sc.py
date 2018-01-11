#!/usr/bin/python3.6

import argparse
import logging
import subprocess
import time
from distutils.dir_util import copy_tree
from os.path import abspath

import coloredlogs

from bot_factory import retrieve_bots
from bot_storage import LocalBotStorage, SscaitBotStorage
from docker import launch_image, check_docker_requirements, running_containers, BASE_VNC_PORT
from game import GameType
from map import check_map_exists, SC_MAP_DIR
from player import HumanPlayer, PlayerRace, bot_regex, SC_BOT_DIR, BotPlayer
from utils import random_string

# Default bot dirs
SC_LOG_DIR = abspath("logs")
SC_BWAPI_DATA_BWTA_DIR = abspath("bwapi-data/BWTA")
SC_BWAPI_DATA_BWTA2_DIR = abspath("bwapi-data/BWTA2")
SC_BOT_DATA_READ_DIR = abspath("bot-data/read")
SC_BOT_DATA_WRITE_DIR = abspath("bot-data/write")
SC_BOT_DATA_LOGS_DIR = abspath("bot-data/logs")

SC_IMAGE = "ggaic/starcraft:play"

parser = argparse.ArgumentParser(
    description='Launch StarCraft docker images for bot/human headless/headful play',
    formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('--bots', nargs="+", required=True, type=bot_regex,
                    metavar="BOT_NAME:RACE",
                    help='Specify the names of the bots that should play.\n'
                         f'RACE can be one of {[race.value for race in PlayerRace]} \n'
                         'If RACEs aren\'t specified\n'
                         'they will be loaded from cache if possible.\n'
                         'The bots are looked up in the --bot_dir directory.\n'
                         'If some does not exist, launcher \n'
                         'will try to download it from SSCAIT server.\n'
                         'Examples: \n'
                         '  --bots Tyr:P PurpleWave:P\n'
                         '  --bots Tyr PurpleWave '
                    )
parser.add_argument('--human', action='store_true',
                    help="Allow play as human against bot.\n")

# todo: support builtin AI
# parser.add_argument('--builtin_ai', type=int, default=0,
#                     help="Add builtin (default) AI to play against.\n"
#                          "Specify how many AIs will play the game. (default 0)")

parser.add_argument('--map', type=str, metavar="MAP.scx", default="sscai/(2)Benzene.scx",
                    help="Name of map on which SC should be played, "
                         "relative to --map_dir")
parser.add_argument('--headless', action='store_true',
                    help="Launch play in headless mode. \n"
                         "No VNC viewer will be launched.")

# Game settings
parser.add_argument("--game_name", type=str, default=random_string(8),
                    help="Override the auto-generated game name")
parser.add_argument("--game_type", type=str, metavar="GAME_TYPE",
                    default=GameType.FREE_FOR_ALL.value,
                    choices=[game_type.value for game_type in GameType],
                    help="Set game type. It can be one of:\n- " +
                         "\n- ".join([game_type.value for game_type in GameType]))
parser.add_argument("--game_speed", type=int, default=0,
                    help="Set game speed (pause of ms between frames), use -1 for game default.")

# Volumes
parser.add_argument('--bot_dir', type=str, default=SC_BOT_DIR)
parser.add_argument('--log_dir', type=str, default=SC_LOG_DIR)
parser.add_argument('--map_dir', type=str, default=SC_MAP_DIR)

#  BWAPI data volumes
parser.add_argument('--bwapi_data_bwta_dir', type=str, default=SC_BWAPI_DATA_BWTA_DIR)
parser.add_argument('--bwapi_data_bwta2_dir', type=str, default=SC_BWAPI_DATA_BWTA2_DIR)

# VNC
parser.add_argument('--vnc_base_port', type=int, default=BASE_VNC_PORT)

# Settings
parser.add_argument('--show_all', action="store_true",
                    help="Launch VNC viewers for all containers, not just the server.")
parser.add_argument('--log_level', type=str, default="INFO",
                    choices=['DEBUG', 'INFO', 'WARN', 'ERROR'],
                    help="Logging level.")
parser.add_argument('--read_overwrite', action="store_true",
                    help="At the end of each game, take the contents of 'write' directory\n"
                         "and copy them over to read directory of the bot.\n"
                         "Needs to be explicitly turned on.")
parser.add_argument('--docker_image', type=str, default=SC_IMAGE,
                    help="The name of the image that should be used to launch the game.\n"
                         "This helps with local development.")
parser.add_argument('--opt', nargs="+",
                    help="Specify custom docker run options")

# todo: add support for multi-PC play.
# We need to think about how to setup docker IPs,
# maybe we will need to specify manually routing tables? :/

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    args = parser.parse_args()
    coloredlogs.install(level=args.log_level)

    check_docker_requirements()
    check_map_exists(args.map_dir + "/" + args.map)

    if args.human and args.headless:
        raise Exception("Cannot use human play in headless mode")

    game_name = "GAME_" + args.game_name

    players = []
    if args.human:
        players.append(HumanPlayer())

    bot_storages = (LocalBotStorage(args.bot_dir), SscaitBotStorage(args.bot_dir))
    players += retrieve_bots(args.bots, bot_storages)

    launch_params = dict(
        # game settings
        headless=args.headless,
        game_name=game_name,
        map_name=args.map,
        game_type=GameType(args.game_type),
        game_speed=args.game_speed,

        # mount dirs
        log_dir=args.log_dir,
        bot_dir=args.bot_dir,
        map_dir=args.map_dir,
        bwapi_data_bwta_dir=args.bwapi_data_bwta_dir,
        bwapi_data_bwta2_dir=args.bwapi_data_bwta2_dir,

        # vnc
        vnc_base_port=args.vnc_base_port,

        # docker
        docker_image=args.docker_image,
        docker_opts=args.opt
    )

    logger.info(f"Logs can be found in {args.log_dir}/GAME_{args.game_name}_*")

    for i, player in enumerate(players):
        launch_image(player, nth_player=i, num_players=len(players), **launch_params)

    logger.info("Checking if game has launched properly...")
    time.sleep(2)
    containers = running_containers(game_name)
    if len(containers) != len(players):
        raise Exception("Some containers exited prematurely, please check logs")

    if not args.headless:
        time.sleep(1)

        for i, player in enumerate(players if args.show_all else players[:1]):
            port = args.vnc_base_port + i
            logger.info(f"Launching vnc viewer for {player} on port {port}")
            subprocess.call(f"vnc-viewer localhost:{port} &", shell=True)

        logger.info("\n"
                    "In headful mode, you must specify and start the game manually.\n"
                    "Select the map, wait for bots to join the game "
                    "and then start the game.")

    logger.info("Waiting until game is finished...")
    while len(running_containers(game_name)) > 0:
        logger.debug("sleep")
        time.sleep(3)

    if args.read_overwrite:
        logger.info("Overwriting bot files")
        for nth_player, player in enumerate(players):
            if isinstance(player, BotPlayer):
                logger.debug(f"Overwriting files for {player}")
                copy_tree(f"{player.write_dir}/{game_name}_{nth_player}", player.read_dir)

    logger.info("Game finished! :)")
