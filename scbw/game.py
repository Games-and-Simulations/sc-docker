import glob
import logging
import os
import signal
import time
from argparse import Namespace
import numpy as np
from .bot_factory import retrieve_bots
from .bot_storage import LocalBotStorage, SscaitBotStorage
from .docker import launch_game, stop_containers
from .error import GameException
from .game_type import GameType
from .player import HumanPlayer, Player
from .vnc import check_vnc_exists
logger = logging.getLogger(__name__)


def find_replays(map_dir, game_name):
    return (glob.glob(
        ('%s/replays/*-*-*_%s_*.rep' % (map_dir, game_name))) + glob.glob(
            ('%s/replays/*-*-*_%s_*.REP' % (map_dir, game_name))))


def find_winner(game_name, map_dir, num_players):
    replay_files = find_replays(map_dir, game_name)
    if (len(replay_files) != num_players):
        logger.info('Found replay files:')
        logger.info(replay_files)
        raise GameException(("""The game '%s' did not finish properly! 
Did not find replay files from all players in '%s/replays/'.""" % (game_name,
                                                                   map_dir)))
    replay_sizes = map(os.path.getsize, replay_files)
    winner_idx = np.argmax(replay_sizes)
    winner_file = replay_files[winner_idx]
    nth_player = winner_file.replace('.rep', '').replace('.REP',
                                                         '').split('_')[(-1)]
    return int(nth_player)


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


class GameResult():
    def __init__(self, game_name, game_time, winner_player, players,
                 replay_files, log_files):
        self.game_name = game_name
        self.game_time = game_time
        self.winner_player = winner_player
        self.players = players
        self.replay_files = replay_files
        self.log_files = log_files


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
    try:
        time_start = time.time()
        launch_game(players, launch_params, args.show_all, args.read_overwrite,
                    wait_callback)
        game_time = (time.time() - time_start)
        log_files = glob.glob(('%s/*%s*.log' % (args.log_dir, game_name)))
        replay_files = find_replays(args.map_dir, game_name)
        winner_player = find_winner(game_name, args.map_dir, len(players))
        return GameResult(game_name, game_time, winner_player, players,
                          replay_files, log_files)
    except KeyboardInterrupt:
        logger.warning('Caught interrupt, shutting down containers')
        logger.warning('This can take a moment, please wait.')
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        stop_containers(game_name)
        logger.info(('Game cancelled.' % ()))
        raise
