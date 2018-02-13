import glob
import logging
import signal
import time
from argparse import Namespace
from typing import List, Optional, Callable

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


def find_replays(map_dir: str, game_name: str):
    return glob.glob(f"{map_dir}/replays/{game_name}_*.rep") + \
           glob.glob(f"{map_dir}/replays/{game_name}_*.REP")


def find_results(log_dir: str, game_name: str):
    return glob.glob(f"{log_dir}/{game_name}_*_results.json")


def find_frames(log_dir: str, game_name: str):
    return glob.glob(f"{log_dir}/{game_name}_*_frames.csv")


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
    vnc_host: str
    show_all: bool
    read_overwrite: bool
    docker_image: str
    opt: str


def run_game(args: GameArgs, wait_callback: Optional[Callable] = None) -> Optional[GameResult]:
    # Check all startup requirements
    if not args.headless:
        check_vnc_exists()
    if args.human and args.headless:
        raise GameException("Cannot use human play in headless mode")
    if args.headless and args.show_all:
        raise GameException("Cannot show all screens in headless mode")

    # Each game is prefixed with "GAME_"
    # this is needed for game filtering in docker ps
    game_name = "GAME_" + args.game_name

    # Prepare players
    players = []
    if args.human:
        players.append(HumanPlayer())
    if args.bots is None:
        args.bots = []
    bot_storages = (LocalBotStorage(args.bot_dir), SscaitBotStorage(args.bot_dir))
    players += retrieve_bots(args.bots, bot_storages)

    is_bots_1v1_game = len(players) == 2 and not args.human

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
        vnc_host=args.vnc_host,

        # docker
        docker_image=args.docker_image,
        docker_opts=opts
    )

    time_start = time.time()
    is_realtime_outed = False
    try:
        launch_game(players, launch_params,
                    args.show_all, args.read_overwrite,
                    wait_callback)

    except RealtimeOutedException:
        is_realtime_outed = True

    except KeyboardInterrupt:
        logger.warning("Caught interrupt, shutting down containers")
        logger.warning("This can take a moment, please wait.")

        # prevent another throw of KeyboardInterrupt exception
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        stop_containers(game_name)
        logger.info(f"Game cancelled.")
        raise

    if is_bots_1v1_game:
        game_time = time.time() - time_start

        log_files = find_logs(args.log_dir, game_name)
        replay_files = find_replays(args.map_dir, game_name)
        frame_files = find_frames(args.log_dir, game_name)
        result_files = find_results(args.log_dir, game_name)

        return GameResult(game_name, players, game_time,
                          # game error states
                          is_realtime_outed,
                          # game files
                          replay_files, log_files, frame_files, result_files)

    return None
