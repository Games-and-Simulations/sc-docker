import glob
import logging
import os
import signal
import time
from argparse import Namespace
from typing import List, Optional, Callable

import numpy as np

from .bot_factory import retrieve_bots
from .bot_storage import LocalBotStorage, SscaitBotStorage
from .docker import launch_game, stop_containers
from .error import GameException
from .game_type import GameType
from .player import HumanPlayer, Player
from .vnc import check_vnc_exists

logger = logging.getLogger(__name__)


def find_replays(map_dir: str, game_name: str):
    return glob.glob(f"{map_dir}/replays/*-*-*_{game_name}_*.rep") + \
           glob.glob(f"{map_dir}/replays/*-*-*_{game_name}_*.REP")


def find_winner(game_name: str, map_dir: str, num_players: int) -> int:
    replay_files = find_replays(map_dir, game_name)
    if len(replay_files) != num_players:
        logger.info("Found replay files:")
        logger.info(replay_files)
        raise GameException(f"The game '{game_name}' did not finish properly! \n"
                            f"Did not find replay files from all players in '{map_dir}/replays/'.")

    replay_sizes = map(os.path.getsize, replay_files)

    winner_idx = np.argmax(replay_sizes)
    winner_file = replay_files[winner_idx]
    nth_player = winner_file.replace(".rep", "").replace(".REP", "").split("_")[-1]
    return int(nth_player)


class GameArgs(Namespace):
    bots: List[str]
    human: bool
    map: str
    headless: bool
    game_name: str
    game_type: str
    game_speed: int
    timeout: int
    bot_dir: str
    log_dir: str
    map_dir: str
    bwapi_data_bwta_dir: str
    bwapi_data_bwta2_dir: str
    vnc_base_port: int
    show_all: bool
    read_overwrite: bool
    docker_image: str
    opt: str


class GameResult:
    def __init__(self, game_name: str,
                 game_time: float,
                 winner_player: int,
                 players: List[Player],
                 replay_files: List[str],
                 log_files: List[str]):
        self.game_name = game_name
        self.game_time = game_time
        self.winner_player = winner_player
        self.players = players
        self.replay_files = replay_files
        self.log_files = log_files


def run_game(args: GameArgs, wait_callback: Optional[Callable] = None) -> GameResult:
    # See CLI parser for required args

    # Check all startup requirements
    if not args.headless:
        check_vnc_exists()
    if args.human and args.headless:
        raise GameException("Cannot use human play in headless mode")
    if args.headless and args.show_all:
        raise GameException("Cannot show all screens in headless mode")

    # Prepare players
    game_name = "GAME_" + args.game_name

    players = []
    if args.human:
        players.append(HumanPlayer())
    if args.bots is None:
        args.bots = []

    bot_storages = (LocalBotStorage(args.bot_dir), SscaitBotStorage(args.bot_dir))
    players += retrieve_bots(args.bots, bot_storages)

    opts = [] if not args.opt else args.opt.split(" ")

    # Prepare game launching
    launch_params = dict(
        # game settings
        headless=args.headless,
        game_name=game_name,
        map_name=args.map,
        game_type=GameType(args.game_type),
        game_speed=args.game_speed,
        timeout=args.timeout,

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
        docker_opts=opts
    )

    try:
        time_start = time.time()
        launch_game(players, launch_params, args.show_all, args.read_overwrite, wait_callback)
        game_time = time.time() - time_start
        log_files = glob.glob(f"{args.log_dir}/*{game_name}*.log")
        replay_files = find_replays(args.map_dir, game_name)
        winner_player = find_winner(game_name, args.map_dir, len(players))

        return GameResult(game_name, game_time, winner_player, players, replay_files, log_files)

    except KeyboardInterrupt:
        logger.warning("Caught interrupt, shutting down containers")
        logger.warning("This can take a moment, please wait.")

        # prevent another throw of KeyboardInterrupt exception
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        stop_containers(game_name)
        logger.info(f"Game cancelled.")
        raise
