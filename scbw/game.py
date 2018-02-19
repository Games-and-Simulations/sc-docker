import logging
import signal
import time
from argparse import Namespace
from .bot_factory import retrieve_bots
from .bot_storage import LocalBotStorage, SscaitBotStorage
from .docker import launch_game, stop_containers, dockermachine_ip, cleanup_containers, running_containers
from .error import GameException, RealtimeOutedException
from .game_type import GameType
from .logs import find_logs, find_frames, find_replays, find_results
from .player import HumanPlayer
from .plot import RealtimeFramePlotter
from .result import GameResult
from .vnc import check_vnc_exists
logger = logging.getLogger(__name__)


class GameArgs(Namespace):
    bots = None
    human = None
    map = None
    headless = None
    game_name = None
    game_type = None
    game_speed = None
    hide_names = None
    timeout = None
    bot_dir = None
    log_dir = None
    map_dir = None
    bwapi_data_bwta_dir = None
    bwapi_data_bwta2_dir = None
    vnc_base_port = None
    vnc_host = None
    show_all = None
    plot_realtime = None
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
    is_1v1_game = (len(players) == 2)
    opts = ([] if (not args.opt) else args.opt.split(' '))
    if (args.vnc_host == ''):
        args.vnc_host = (dockermachine_ip() or 'localhost')
        logger.debug(("Using vnc host '%s'" % (args.vnc_host, )))
    if args.plot_realtime:
        plot_realtime = RealtimeFramePlotter(args.log_dir, game_name, players)

        def _wait_callback():
            plot_realtime.redraw()
            if (wait_callback is not None):
                wait_callback()
            else:
                time.sleep(3)
    else:
        _wait_callback = wait_callback
    launch_params = dict(
        headless=args.headless,
        game_name=game_name,
        map_name=args.map,
        game_type=GameType(args.game_type),
        game_speed=args.game_speed,
        timeout=args.timeout,
        hide_names=args.hide_names,
        log_dir=args.log_dir,
        bot_dir=args.bot_dir,
        map_dir=args.map_dir,
        bwapi_data_bwta_dir=args.bwapi_data_bwta_dir,
        bwapi_data_bwta2_dir=args.bwapi_data_bwta2_dir,
        vnc_base_port=args.vnc_base_port,
        vnc_host=args.vnc_host,
        docker_image=args.docker_image,
        docker_opts=opts)
    time_start = time.time()
    is_realtime_outed = False
    try:
        launch_game(players, launch_params, args.show_all, args.read_overwrite,
                    _wait_callback)
    except RealtimeOutedException:
        is_realtime_outed = True
    except KeyboardInterrupt:
        logger.warning('Caught interrupt, shutting down containers')
        logger.warning('This can take a moment, please wait.')
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        containers = running_containers(game_name)
        stop_containers(containers)
        logger.debug('Removing game containers')
        cleanup_containers(containers)
        logger.info(('Game cancelled.' % ()))
        raise
    if args.plot_realtime:
        plot_realtime.save(('%s/%s_frameplot.png' % (args.log_dir, game_name)))
    if is_1v1_game:
        game_time = (time.time() - time_start)
        log_files = find_logs(args.log_dir, game_name)
        replay_files = find_replays(args.map_dir, game_name)
        frame_files = find_frames(args.log_dir, game_name)
        result_files = find_results(args.log_dir, game_name)
        return GameResult(game_name, players, game_time, is_realtime_outed,
                          replay_files, log_files, frame_files, result_files)
    return None
