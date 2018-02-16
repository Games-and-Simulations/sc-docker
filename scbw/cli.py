import argparse
import logging
import sys
from os.path import exists

import coloredlogs

from .defaults import *
from .docker import BASE_VNC_PORT, VNC_HOST
from .error import ScbwException
from .game import run_game, GameType
from .player import PlayerRace, bot_regex
from .utils import random_string

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(
    description='Launch StarCraft docker images for bot/human headless/headful play',
    formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument('--install', action='store_true',
                    help="Download all dependencies and data files.\n"
                         "Needed to run the first time after `pip install`.")

parser.add_argument('--bots', nargs="+", type=bot_regex,
                    metavar="BOT_NAME[:RACE]",
                    help='Specify the names of the bots that should play.\n'
                         f'Optional RACE can be one of {[race.value for race in PlayerRace]} \n'
                         'If RACE isn\'t specified it will be loaded from cache if possible.\n'
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
                    help="Name of map on which SC should be played,\n"
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
                    help="Set game speed (pause of ms between frames),\n"
                         "use -1 for game default.")
parser.add_argument("--timeout", type=int, default=None,
                    help="Kill docker container after timeout seconds.\n"
                         "If not set, run without timeout.")
parser.add_argument("--hide_names", action="store_true",
                    help="Hide player names, each player will be called only 'player'.\n"
                         "By default, show player names (as their bot name)")

# Volumes
parser.add_argument('--bot_dir', type=str, default=SC_BOT_DIR,
                    help=f"Directory where bots are stored, default:\n{SC_BOT_DIR}")
parser.add_argument('--log_dir', type=str, default=SC_LOG_DIR,
                    help=f"Directory where logs are stored, default:\n{SC_LOG_DIR}")
parser.add_argument('--map_dir', type=str, default=SC_MAP_DIR,
                    help=f"Directory where maps are stored, default:\n{SC_MAP_DIR}")

#  BWAPI data volumes
parser.add_argument('--bwapi_data_bwta_dir', type=str, default=SC_BWAPI_DATA_BWTA_DIR,
                    help=f"Directory where BWTA map caches are stored, "
                         f"default:\n{SC_BWAPI_DATA_BWTA_DIR}")
parser.add_argument('--bwapi_data_bwta2_dir', type=str, default=SC_BWAPI_DATA_BWTA2_DIR,
                    help=f"Directory where BWTA2 map caches are stored, "
                         f"default:\n{SC_BWAPI_DATA_BWTA2_DIR}")

# VNC
parser.add_argument('--vnc_base_port', type=int, default=BASE_VNC_PORT,
                    help="VNC lowest port number (for server).\n"
                         "Each consecutive n-th client (player)\n"
                         "has higher port number - vnc_base_port+n ")
parser.add_argument('--vnc_host', type=str, default='',
                    help="Address of the host on which VNC connections would be accessible\n"
                         f"default:\n{VNC_HOST} or IP address of the docker-machine")

# Settings
parser.add_argument('--show_all', action="store_true",
                    help="Launch VNC viewers for all containers, not just the server.")
parser.add_argument('--log_level', type=str, default="INFO",
                    choices=['DEBUG', 'INFO', 'WARN', 'ERROR'],
                    help="Logging level.")
parser.add_argument('--log_verbose', action="store_true",
                    help="Add more information to logging, as time and PID.")
parser.add_argument('--read_overwrite', action="store_true",
                    help="At the end of each game, copy the contents\n"
                         "of 'write' directory to the read directory\n"
                         "of the bot.\n"
                         "Needs to be explicitly turned on.")
parser.add_argument('--docker_image', type=str, default=SC_IMAGE,
                    help="The name of the image that should \n"
                         "be used to launch the game.\n"
                         "This helps with local development.")
parser.add_argument('--opt', type=str,
                    help="Specify custom docker run options")
parser.add_argument('--plot_realtime', action='store_true',
                    help="Allow realtime plotting of frame information.\n"
                         "At the end of the game, this plot will be saved\n"
                         "to file {LOG_DIR}/{GAME_NAME}_frameplot.png")

parser.add_argument('-v', "--version", action='store_true', dest='show_version',
                    help="Show current version")


# todo: add support for multi-PC play.
# We need to think about how to setup docker IPs,
# maybe we will need to specify manually routing tables? :/

def main():
    args = parser.parse_args()
    if args.show_version:
        print(VERSION)
        sys.exit(0)

    coloredlogs.install(
        level=args.log_level,
        fmt="%(asctime)s %(levelname)s %(name)s[%(process)d] %(message)s" if args.log_verbose
        else "%(levelname)s %(message)s")

    if args.install:
        from .install import install
        try:
            install()
            sys.exit(0)
        except ScbwException as e:
            logger.exception(e)
            sys.exit(1)
        except KeyboardInterrupt:
            sys.exit(1)

    if not exists(SCBW_BASE_DIR):
        parser.error(f'The data directory {SCBW_BASE_DIR} was not found. '
                     f'Did you run "scbw.play --install"?')
        # parser.error exits

    # bots are always required, but not if showing version :)
    if not args.bots and not args.human:
        parser.error('the following arguments are required: --bots or --human')
        # parser.error exits

    try:
        game_result = run_game(args)
        if game_result is None:
            logger.info("Game results are available only for 1v1 (bot vs bot) games.")
            sys.exit(0)

        logger.info(f"Game {game_result.game_name} "
                    f"finished in {game_result.game_time:.2f} seconds.")
        logger.info("---")
        logger.info("Logs are saved here:")
        for log_file in sorted(game_result.log_files):
            logger.info(log_file)
        logger.info("---")

        logger.info("Replays are saved here:")
        for replay_file in sorted(game_result.replay_files):
            logger.info(replay_file)
        logger.info("---")

        logger.info("Frame information is saved here:")
        for frame_file in sorted(game_result.frame_files):
            logger.info(frame_file)
        logger.info("---")

        logger.info("Game results are saved here:")
        for frame_file in sorted(game_result.result_files):
            logger.info(frame_file)
        logger.info("---")

        if game_result.is_valid:
            logger.info(f"Winner is {game_result.winner_player} "
                        f"(player {game_result.nth_winner_player})")

            # the only print! Everything else goes to stderr!
            print(game_result.nth_winner_player)
            sys.exit(0)

        if game_result.is_realtime_outed:
            logger.error("Game has realtime outed!")
            sys.exit(1)
        if game_result.is_gametime_outed:
            logger.error("Game has gametime outed!")
            sys.exit(1)
        if game_result.is_crashed:
            logger.error("Game has crashed!")
            sys.exit(1)

    except ScbwException as e:
        logger.exception(e)
        sys.exit(1)

    except KeyboardInterrupt:
        sys.exit(1)
