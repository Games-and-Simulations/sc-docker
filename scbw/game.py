import enum
import glob
import json
import logging
import os
import signal
import time
from argparse import Namespace
from typing import List, Optional, Callable

from scbw.bot_factory import retrieve_bots
from scbw.bot_storage import LocalBotStorage, SscaitBotStorage
from scbw.docker_utils import (
    dockermachine_ip, launch_game,
    remove_game_containers
)
from scbw.error import GameException, RealtimeOutedException
from scbw.game_type import GameType
from scbw.player import HumanPlayer, BotPlayer
from scbw.plot import RealtimeFramePlotter
from scbw.result import GameResult
from scbw.vnc import check_vnc_exists

logger = logging.getLogger(__name__)


class GameArgs(Namespace):
    bots: List[str]
    human: bool
    map: str
    headless: bool
    game_name: str
    game_type: str
    game_speed: int
    seed_override: int
    hide_names: bool
    random_names: bool
    timeout: int
    timeout_at_frame: int
    bot_dir: str
    game_dir: str
    map_dir: str
    bwapi_data_bwta_dir: str
    bwapi_data_bwta2_dir: str
    vnc_base_port: int
    vnc_host: str
    capture_movement: bool
    auto_launch: bool
    show_all: bool
    allow_input: bool
    plot_realtime: bool
    read_overwrite: bool
    docker_image: str
    nano_cpus: int
    mem_limit: str


def run_game(
        args: GameArgs,
        wait_callback: Optional[Callable] = None
) -> Optional[GameResult]:
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

    bot_storages = (
        LocalBotStorage(args.bot_dir),
        SscaitBotStorage(args.bot_dir)
    )
    players += retrieve_bots(args.bots, bot_storages)

    is_1v1_game = len(players) == 2

    if args.vnc_host == "":
        args.vnc_host = dockermachine_ip() or "localhost"
        logger.debug(f"Using vnc host '{args.vnc_host}'")

    # make sure we always have a sleeping wait callback!
    if wait_callback is None:
        wait_callback = lambda: time.sleep(3)

    if args.plot_realtime:
        plot_realtime = RealtimeFramePlotter(args.game_dir, game_name, players)

        def _wait_callback():
            plot_realtime.redraw()
            wait_callback()
    else:
        _wait_callback = wait_callback

    # Seed override is empty string if not specified, integer otherwise
    seed_override = ""
    if args.seed_override is not None:
        seed_override = str(args.seed_override)

    # Prepare game launching
    launch_params = dict(
        # game settings
        headless=args.headless,
        game_name=game_name,
        map_name=args.map,
        game_type=GameType(args.game_type),
        game_speed=args.game_speed,
        seed_override=seed_override,
        timeout=args.timeout,
        timeout_at_frame=args.timeout_at_frame,
        hide_names=args.hide_names,
        drop_players=any(isinstance(player, BotPlayer)
                         and player.meta.javaDebugPort is not None
                         for player in players),
        allow_input=args.allow_input,
        auto_launch=args.auto_launch,
        random_names=args.random_names,

        # mount dirs
        game_dir=args.game_dir,
        bot_dir=args.bot_dir,
        map_dir=args.map_dir,
        bwapi_data_bwta_dir=args.bwapi_data_bwta_dir,
        bwapi_data_bwta2_dir=args.bwapi_data_bwta2_dir,

        # vnc
        vnc_base_port=args.vnc_base_port,
        vnc_host=args.vnc_host,
        capture_movement=args.capture_movement,

        # docker
        docker_image=args.docker_image,
        nano_cpus=args.nano_cpus,
        mem_limit=args.mem_limit
    )

    time_start = time.time()
    is_realtime_outed = False
    try:
        launch_game(
            players, launch_params, args.show_all,
            args.read_overwrite, _wait_callback
        )
    except RealtimeOutedException:
        is_realtime_outed = True
        logger.debug(f"Game timed out")

    except KeyboardInterrupt:
        logger.warning("Caught interrupt, shutting down containers")
        logger.warning("This can take a moment, please wait.")

        # prevent another throw of KeyboardInterrupt exception
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        remove_game_containers(game_name)
        logger.info(f"Game cancelled.")
        raise

    if args.plot_realtime:
        plot_realtime.save(f"{args.game_dir}/{game_name}/frame_plot.png")

    # move replay files
    replay_files = set(
        # there are at most 8 players for a game
        glob.glob(f"{args.map_dir}/replays/{game_name}_[0-7].rep") +
        glob.glob(f"{args.map_dir}/replays/{game_name}_[0-7].REP")
    )
    for replay_file in replay_files:
        nth_player = int(replay_file[:-4].split("_")[-1])
        os.rename(replay_file, f"{args.game_dir}/{game_name}/player_{nth_player}.rep")

    if is_1v1_game:
        game_time = time.time() - time_start
        game_result = GameResult(
            game_name, players, game_time,
            # game error states
            is_realtime_outed,
            # dirs with results
            args.map_dir, args.game_dir
        )

        info = launch_params.copy()
        info.update(dict(
            read_overwrite=args.read_overwrite,
            bots=args.bots,

            is_crashed=game_result.is_crashed,
            is_gametime_outed=game_result.is_gametime_outed,
            is_realtime_outed=game_result.is_realtime_outed,
            game_time=game_result.game_time,

            winner=None,
            loser=None,
            winner_race=None,
            loser_race=None,
        ))
        if game_result.is_valid:
            info.update(dict(
                winner=game_result.winner_player.name,
                loser=game_result.loser_player.name,
                winner_race=game_result.winner_player.race.value,
                loser_race=game_result.loser_player.race.value,
            ))

        logger.debug(info)
        with open(f"{args.game_dir}/{game_name}/result.json", "w") as f:
            json.dump(info, f, cls=EnumEncoder)
        logger.info(f"game {game_name} recorded")

        return game_result

    return None


class EnumEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, enum.Enum):
            return obj.value
        return super(EnumEncoder, self).default(obj)
