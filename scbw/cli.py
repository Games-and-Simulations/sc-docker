import argparse
import logging

import coloredlogs

from .docker import BASE_VNC_PORT
from .game import run_game, GameType
from .player import PlayerRace, bot_regex
from .utils import random_string, get_data_dir

logger = logging.getLogger(__name__)

# Default bot dirs
SCBW_BASE_DIR = get_data_dir()
SC_LOG_DIR = f"{SCBW_BASE_DIR}/logs"
SC_BWAPI_DATA_BWTA_DIR = f"{SCBW_BASE_DIR}/bwapi-data/BWTA"
SC_BWAPI_DATA_BWTA2_DIR = f"{SCBW_BASE_DIR}/bwapi-data/BWTA2"
SC_BOT_DIR = f"{SCBW_BASE_DIR}/bots"
SC_MAP_DIR = f"{SCBW_BASE_DIR}/maps"

SC_IMAGE = "starcraft:game"

parser = argparse.ArgumentParser(
    description='Launch StarCraft docker images for bot/human headless/headful play',
    formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('--bots', nargs="+", required=True, type=bot_regex,
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

# Settings
parser.add_argument('--show_all', action="store_true",
                    help="Launch VNC viewers for all containers, not just the server.")
parser.add_argument('--log_level', type=str, default="INFO",
                    choices=['DEBUG', 'INFO', 'WARN', 'ERROR'],
                    help="Logging level.")
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
parser.add_argument('--disable_checks', action='store_true',
                    help="Disable docker and other checks, useful for repeated launching.")


# todo: add support for multi-PC play.
# We need to think about how to setup docker IPs,
# maybe we will need to specify manually routing tables? :/

def main():
    args = parser.parse_args()
    coloredlogs.install(level=args.log_level, fmt="%(levelname)s %(message)s")
    game_result = run_game(args)

    logger.info(f"Game {game_result.game_name} finished in {game_result.game_time:.2f} seconds.")
    logger.info("Logs are saved here:")
    for log_file in game_result.log_files:
        logger.info(log_file)

    logger.info("Replays are saved here:")
    for replay_file in game_result.replay_files:
        logger.info(replay_file)

    logger.info(f"Winner is {game_result.players[game_result.winner_player]} "
                f"(player {game_result.winner_player})")

    # the only print! Everything else goes to stderr!
    print(game_result.winner_player)
