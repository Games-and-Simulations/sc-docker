import glob
import logging
import signal
import time
from argparse import Namespace
from .bot_factory import retrieve_bots
from .bot_storage import LocalBotStorage, SscaitBotStorage
from .docker import launch_game, stop_containers
from .error import GameException, RealtimeOutedException
from .game_type import GameType
from .logs import find_logs
from .player import HumanPlayer
from .result import GameResult
from .vnc import check_vnc_exists
logger = logging.getLogger(__name__)


def find_replays(map_dir, game_name):
    return (glob.glob(
        ('%s/replays/%s_*.rep' % (map_dir, game_name))) + glob.glob(
            ('%s/replays/%s_*.REP' % (map_dir, game_name))))


def find_results(log_dir, game_name):
    return glob.glob(('%s/%s_*_results.json' % (log_dir, game_name)))


def find_frames(log_dir, game_name):
    return glob.glob(('%s/%s_*_frames.csv' % (log_dir, game_name)))


class GameArgs(Namespace):
    bots = None
    human = None
    map = None
    headless = None
    game_name = None
    game_type = None
    game_speed = None
    timeout = None
    bot_dir = None
    log_dir = None
    map_dir = None
    bwapi_data_bwta_dir = None
    bwapi_data_bwta2_dir = None
    vnc_base_port = None
    show_all = None
    read_overwrite = None
    docker_image = None
    opt = None


def run_game(args, wait_callback=None):
    if (not args.headless):
        check_vnc_exists()
    if (args.human and args.headless):
        raise GameException('Cannot use human play in headless mode')
    if (args.headless and args.show_all):
        raise GameException('Cannot show all screens in headless mode')
    game_name = ('GAME_' + args.game_name)
    players = []
    if args.human:
        players.append(HumanPlayer())
    if (args.bots is None):
        args.bots = []
    bot_storages = (LocalBotStorage(args.bot_dir),
                    SscaitBotStorage(args.bot_dir))
    players += retrieve_bots(args.bots, bot_storages)
    is_bots_1v1_game = ((len(players) == 2) and (not args.human))
    opts = ([] if (not args.opt) else args.opt.split(' '))
    launch_params = dict(
        headless=args.headless,
        game_name=game_name,
        map_name=args.map,
        game_type=GameType(args.game_type),
        game_speed=args.game_speed,
        timeout=args.timeout,
        log_dir=args.log_dir,
        bot_dir=args.bot_dir,
        map_dir=args.map_dir,
        bwapi_data_bwta_dir=args.bwapi_data_bwta_dir,
        bwapi_data_bwta2_dir=args.bwapi_data_bwta2_dir,
        vnc_base_port=args.vnc_base_port,
        docker_image=args.docker_image,
        docker_opts=opts)
    time_start = time.time()
    is_realtime_outed = False
    try:
        launch_game(players, launch_params, args.show_all, args.read_overwrite,
                    wait_callback)
    except RealtimeOutedException:
        is_realtime_outed = True
    except KeyboardInterrupt:
        logger.warning('Caught interrupt, shutting down containers')
        logger.warning('This can take a moment, please wait.')
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        stop_containers(game_name)
        logger.info(('Game cancelled.' % ()))
        raise
    if is_bots_1v1_game:
        game_time = (time.time() - time_start)
        log_files = find_logs(args.log_dir, game_name)
        replay_files = find_replays(args.map_dir, game_name)
        frame_files = find_frames(args.log_dir, game_name)
        result_files = find_results(args.log_dir, game_name)
        return GameResult(game_name, players, game_time, is_realtime_outed,
                          replay_files, log_files, frame_files, result_files)
    return None
