import argparse
import logging
import sys
import coloredlogs
from os.path import exists
from .__init__ import VERSION
from .docker import BASE_VNC_PORT
from .error import ScbwException
from .game import run_game, GameType
from .player import PlayerRace, bot_regex
from .utils import random_string
from .defaults import *
logger = logging.getLogger(__name__)
parser = argparse.ArgumentParser(
    description=
    'Launch StarCraft docker images for bot/human headless/headful play',
    formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument(
    '--install',
    action='store_true',
    help="""Download all dependencies and data files.
Needed to run the first time after `pip install`.""")
parser.add_argument(
    '--bots',
    nargs='+',
    type=bot_regex,
    metavar='BOT_NAME[:RACE]',
    help=("""Specify the names of the bots that should play.
Optional RACE can be one of %s 
If RACE isn't specified it will be loaded from cache if possible.
The bots are looked up in the --bot_dir directory.
If some does not exist, launcher 
will try to download it from SSCAIT server.
Examples: 
  --bots Tyr:P PurpleWave:P
  --bots Tyr PurpleWave """ % ([race.value for race in PlayerRace], )))
parser.add_argument(
    '--human',
    action='store_true',
    help="""Allow play as human against bot.
""")
parser.add_argument(
    '--map',
    type=str,
    metavar='MAP.scx',
    default='sscai/(2)Benzene.scx',
    help="""Name of map on which SC should be played,
relative to --map_dir""")
parser.add_argument(
    '--headless',
    action='store_true',
    help="""Launch play in headless mode. 
No VNC viewer will be launched.""")
parser.add_argument(
    '--game_name',
    type=str,
    default=random_string(8),
    help='Override the auto-generated game name')
parser.add_argument(
    '--game_type',
    type=str,
    metavar='GAME_TYPE',
    default=GameType.FREE_FOR_ALL.value,
    choices=[game_type.value for game_type in GameType],
    help=("""Set game type. It can be one of:
- """ + """
- """.join([game_type.value for game_type in GameType])))
parser.add_argument(
    '--game_speed',
    type=int,
    default=0,
    help="""Set game speed (pause of ms between frames),
use -1 for game default.""")
parser.add_argument(
    '--timeout',
    type=int,
    default=None,
    help="""Kill docker container after timeout seconds.
If not set, run without timeout.""")
parser.add_argument(
    '--bot_dir',
    type=str,
    default=SC_BOT_DIR,
    help=("""Directory where bots are stored, default:
%s""" % (SC_BOT_DIR, )))
parser.add_argument(
    '--log_dir',
    type=str,
    default=SC_LOG_DIR,
    help=("""Directory where logs are stored, default:
%s""" % (SC_LOG_DIR, )))
parser.add_argument(
    '--map_dir',
    type=str,
    default=SC_MAP_DIR,
    help=("""Directory where maps are stored, default:
%s""" % (SC_MAP_DIR, )))
parser.add_argument(
    '--bwapi_data_bwta_dir',
    type=str,
    default=SC_BWAPI_DATA_BWTA_DIR,
    help=("""Directory where BWTA map caches are stored, default:
%s""" % (SC_BWAPI_DATA_BWTA_DIR, )))
parser.add_argument(
    '--bwapi_data_bwta2_dir',
    type=str,
    default=SC_BWAPI_DATA_BWTA2_DIR,
    help=("""Directory where BWTA2 map caches are stored, default:
%s""" % (SC_BWAPI_DATA_BWTA2_DIR, )))
parser.add_argument(
    '--vnc_base_port',
    type=int,
    default=BASE_VNC_PORT,
    help="""VNC lowest port number (for server).
Each consecutive n-th client (player)
has higher port number - vnc_base_port+n """)
parser.add_argument(
    '--show_all',
    action='store_true',
    help='Launch VNC viewers for all containers, not just the server.')
parser.add_argument(
    '--log_level',
    type=str,
    default='INFO',
    choices=['DEBUG', 'INFO', 'WARN', 'ERROR'],
    help='Logging level.')
parser.add_argument(
    '--read_overwrite',
    action='store_true',
    help="""At the end of each game, copy the contents
of 'write' directory to the read directory
of the bot.
Needs to be explicitly turned on.""")
parser.add_argument(
    '--docker_image',
    type=str,
    default=SC_IMAGE,
    help="""The name of the image that should 
be used to launch the game.
This helps with local development.""")
parser.add_argument(
    '--opt', type=str, help='Specify custom docker run options')
parser.add_argument(
    '--disable_checks',
    action='store_true',
    help='Disable docker and other checks, useful for repeated launching.')
parser.add_argument(
    '-v',
    '--version',
    action='store_true',
    dest='show_version',
    help='Show current version')


def main():
    args = parser.parse_args()
    if args.show_version:
        print(VERSION)
        sys.exit(0)
    coloredlogs.install(level=args.log_level, fmt='%(levelname)s %(message)s')
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
    if (not exists(SCBW_BASE_DIR)):
        parser.error((
            'The data directory %s was not found. Did you run "scbw.play --install"?'
            % (SCBW_BASE_DIR, )))
    if ((not args.bots) and (not args.human)):
        parser.error('the following arguments are required: --bots or --human')
    try:
        game_result = run_game(args)
        logger.info(('Game %s finished in %s seconds.' %
                     (game_result.game_name, game_result.game_time)))
        logger.info('Logs are saved here:')
        for log_file in sorted(game_result.log_files):
            logger.info(log_file)
        logger.info('Replays are saved here:')
        for replay_file in sorted(game_result.replay_files):
            logger.info(replay_file)
        logger.info(('Winner is %s (player %s)' %
                     (game_result.players[game_result.winner_player],
                      game_result.winner_player)))
        print(game_result.winner_player)
    except ScbwException as e:
        logger.exception(e)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(1)
