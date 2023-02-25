import argparse
import logging
import os.path
import sys

import coloredlogs
import docker
from scbw.defaults import (
    SC_BOT_DIR, SC_GAME_DIR, SC_MAP_DIR, SCBW_BASE_DIR, SC_IMAGE,
    SC_BWAPI_DATA_BWTA_DIR, SC_BWAPI_DATA_BWTA2_DIR, VERSION
)
from scbw.docker_utils import BASE_VNC_PORT, VNC_HOST
from scbw.error import ScbwException
from scbw.game import run_game
from scbw.game_type import GameType
from scbw.player import bot_regex, PlayerRace
from scbw.utils import random_string

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
parser.add_argument("--seed_override", type=int,
                    help="Set random seed.")
parser.add_argument("--timeout", type=int, default=None,
                    help="Kill docker container after timeout seconds.\n"
                         "If not set, run without timeout.")
parser.add_argument("--timeout_at_frame", type=int, default=None,
                    help="End game after the given frame count.\n"
                         "If not set, run without frame limit.")
parser.add_argument("--hide_names", action="store_true",
                    help="Hide player names, each player will be called only 'player'.\n"
                         "By default, show player names (as their bot name)")
parser.add_argument("--random_names", action="store_true",
                    help="Randomize player names.")
parser.add_argument("--auto_launch", action="store_true",
                    help="In headful mode, automatically launch multiplayer.\n"
                         "Experimental. (automatically sends keys to the starcraft window).")

# Volumes
parser.add_argument('--bot_dir', type=str, default=SC_BOT_DIR,
                    help=f"Directory where bots are stored, default:\n{SC_BOT_DIR}")
parser.add_argument('--game_dir', type=str, default=SC_GAME_DIR,
                    help=f"Directory where game logs and results are stored, default:\n{SC_GAME_DIR}")
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
parser.add_argument('--capture_movement', action="store_true",
                    help="If mouse gets outside of the VNC window, \n"
                         "do not move the game (only use mini map)")

# Settings
parser.add_argument('--show_all', action="store_true",
                    help="Launch VNC viewers for all containers, not just the server.")
parser.add_argument('--allow_input', action="store_true",
                    help="Allow controlling the game for running bots. Useful for debugging.")
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
parser.add_argument('--plot_realtime', action='store_true',
                    help="Allow realtime plotting of frame information.\n"
                         "At the end of the game, this plot will be saved\n"
                         "to file {GAME_DIR}/{GAME_NAME}/frame_plot.png")
parser.add_argument('--mem_limit', type=str, default=None,
                    help="Limit started containers to the given amount of memory.")
parser.add_argument('--nano_cpus', type=int, default=None,
                    help="Limit started containers to the given amount of cpu nanos.")


parser.add_argument('-v', "--version", action='store_true', dest='show_version',
                    help="Show current version")


def _image_version_up_to_date():
    client = docker.from_env()
    return any(tag == SC_IMAGE for image in client.images.list('starcraft') for tag in image.tags)


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

    if args.install or not _image_version_up_to_date():
        from .install import install
        try:
            install()
            if args.install:
                sys.exit(0)
        except ScbwException as e:
            logger.exception(e)
            sys.exit(1)
        except KeyboardInterrupt:
            sys.exit(1)

    if not os.path.exists(SCBW_BASE_DIR):
        parser.error(f'The data directory {SCBW_BASE_DIR} was not found. '
                     f'Did you run "scbw.play --install"?')
        # parser.error exits

    # bots are always required, but not if showing version :)
    if not args.bots and not args.human:
        parser.error('the following arguments are required: --bots or --human')
        # parser.error exits

    if os.path.exists(f"{args.game_dir}/GAME_{args.game_name}"):
        logger.info(f'Game {args.game_name} has already been played, '
                    f'do you wish to continue (and remove logs) ? (Y/n)')
        answer = input()
        if answer.lower() not in ("", "yes", "y"):
            sys.exit(1)

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

        logger.info("Unit event information is saved here:")
        for event_file in sorted(game_result.unit_event_files):
            logger.info(event_file)
        logger.info("---")


        logger.info("Game results are saved here:")
        for score_file in sorted(game_result.score_files):
            logger.info(score_file)
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
