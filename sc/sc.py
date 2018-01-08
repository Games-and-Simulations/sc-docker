#!/usr/bin/python3.6

import argparse
import logging
import subprocess
import time
from os.path import abspath

import coloredlogs

from player import BWAPIVersion, HumanPlayer, Bot, PlayerRace, bot_regex
from bot_retriever import retrieve_bots
from bot_storage import LocalBotStorage
from docker import launch_image, check_docker_requirements
from game import GameType
from utils import random_string

SC_BOT_DIR = abspath("bots")
SC_LOG_DIR = abspath("logs")
SC_MAP_DIR = abspath("maps")

SC_BWAPI_DATA_BWTA_DIR = abspath("bwapi-data/BWTA")
SC_BWAPI_DATA_BWTA2_DIR = abspath("bwapi-data/BWTA2")
SC_BOT_DATA_SAVE_DIR = abspath("bot-data/save")
SC_BOT_DATA_LOGS_DIR = abspath("bot-data/logs")

SC_IMAGE = "ggaic/starcraft:play"

parser = argparse.ArgumentParser(
    description='Launch stacraft docker images for bot/human headless/headful play',
    formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('--bots', nargs="+", required=True, type=bot_regex,
                    metavar="BOT_NAME:RACE:BWAPI_VERSION",
                    help='Specify the names of the bots that should play.\n'
                         f'RACE can be one of {[race.value for race in PlayerRace]} \n'
                         f'BWAPI_VERSION can be one of {[bwapi.value for bwapi in BWAPIVersion]} \n'
                         'If RACE or BWAPI_VERSION aren\'t specified\n'
                         'they will be loaded from cache if possible.\n'
                         'The bots are looked up in the --bot_dir directory.\n'
                         'If some does not exist, launcher \n'
                         'will try to download it from SSCAIT server.\n'
                         'Examples: \n'
                         '  --bots Tyr:P:420 PurpleWave:P\n'
                         '  --bots Tyr::420 PurpleWave '
                    )
parser.add_argument('--human', action='store_true',
                    help="Allow play as human against bot.\n")
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
parser.add_argument("--game_name", type=str, default="GAME_" + random_string(8),
                    help="Override the auto-generated game name")
parser.add_argument("--game_type", type=str, default="MELEE", metavar="GAME_TYPE",
                    choices=[game_type.value for game_type in GameType],
                    help="Set game type. It can be one of:\n- " +
                         "\n- ".join([game_type.value for game_type in GameType]))
parser.add_argument("--game_speed", type=int, default=-1,
                    help="Set game speed (pause of ms between frames), -1 for game default.")

# Volumes
parser.add_argument('--bot_dir', type=str, default=SC_BOT_DIR)
parser.add_argument('--log_dir', type=str, default=SC_LOG_DIR)
parser.add_argument('--map_dir', type=str, default=SC_MAP_DIR)

parser.add_argument('--bwapi_data_bwta_dir', type=str, default=SC_BWAPI_DATA_BWTA_DIR)
parser.add_argument('--bwapi_data_bwta2_dir', type=str, default=SC_BWAPI_DATA_BWTA2_DIR)
parser.add_argument('--bot_data_save_dir', type=str, default=SC_BOT_DATA_SAVE_DIR)
parser.add_argument('--bot_data_logs_dir', type=str, default=SC_BOT_DATA_LOGS_DIR)

# Settings
parser.add_argument('--verbosity', type=str, default="DEBUG",
                    choices=['DEBUG', 'INFO', 'WARN', 'ERROR'],
                    help="Logging level.")
parser.add_argument('--docker_image', type=str, default=SC_IMAGE,
                    help="The name of the image that should be used to launch the game.\n"
                         "This helps with local development.")
parser.add_argument('--opt', nargs="+",
                    help="Specify custom docker run options")

# todo: add support for additional docker options
# todo: add support for multi-PC play
# this includes: networkprovider, lan, localpc, lan-sendto

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    args = parser.parse_args()
    coloredlogs.install(level=args.verbosity)

    check_docker_requirements()

    players = []
    if args.human:
        players.append(HumanPlayer())

    bot_storages = (LocalBotStorage(args.bot_dir),)
    players += retrieve_bots(args.bots, bot_storages)

    launch_params = dict(
        # game settings
        headless=args.headless,
        game_name=args.game_name,
        map_name=args.map,
        game_type=GameType(args.game_type),
        game_speed=args.game_speed,

        # mount dirs
        log_dir=args.log_dir,
        bot_dir=args.bot_dir,
        map_dir=args.map_dir,
        bwapi_data_bwta_dir=args.bwapi_data_bwta_dir,
        bwapi_data_bwta2_dir=args.bwapi_data_bwta2_dir,
        bot_data_save_dir=args.bot_data_save_dir,
        bot_data_logs_dir=args.bot_data_logs_dir,

        # docker
        docker_image=args.docker_image,
        docker_opts=args.opt
    )

    for i, player in enumerate(players):
        if isinstance(player, Bot):
            player.save_settings()

        launch_image(player, nth_player=i, num_players=len(players), **launch_params)

    if not args.headless:
        time.sleep(1)

        for i, player in enumerate(players):
            port = 5900 + i
            logger.info(f"Launching vnc viewer for {player} on port {port}")
            subprocess.call(f"vnc-viewer localhost:{port} &", shell=True)

    time.sleep(5)
