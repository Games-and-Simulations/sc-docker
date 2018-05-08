import enum
import glob
import json
import logging
import os
import signal
import time
from argparse import Namespace
from scbw.bot_factory import retrieve_bots
from scbw.bot_storage import LocalBotStorage, SscaitBotStorage
from scbw.docker_utils import dockermachine_ip, launch_game, remove_game_containers
from scbw.error import GameException, RealtimeOutedException
from scbw.game_type import GameType
from scbw.player import HumanPlayer, BotPlayer
from scbw.plot import RealtimeFramePlotter
from scbw.result import GameResult
from scbw.vnc import check_vnc_exists
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
    random_names = None
    timeout = None
    bot_dir = None
    game_dir = None
    map_dir = None
    bwapi_data_bwta_dir = None
    bwapi_data_bwta2_dir = None
    vnc_base_port = None
    vnc_host = None
    capture_movement = None
    auto_launch = None
    show_all = None
    allow_input = None
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
    if (wait_callback is None):
        wait_callback = (lambda: time.sleep(3))
    if args.plot_realtime:
        plot_realtime = RealtimeFramePlotter(args.game_dir, game_name, players)

        def _wait_callback():
            plot_realtime.redraw()
            wait_callback()
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
        drop_players=any(((isinstance(player, BotPlayer) and
                           (player.meta.javaDebugPort is not None))
                          for player in players)),
        allow_input=args.allow_input,
        auto_launch=args.auto_launch,
        random_names=args.random_names,
        game_dir=args.game_dir,
        bot_dir=args.bot_dir,
        map_dir=args.map_dir,
        bwapi_data_bwta_dir=args.bwapi_data_bwta_dir,
        bwapi_data_bwta2_dir=args.bwapi_data_bwta2_dir,
        vnc_base_port=args.vnc_base_port,
        vnc_host=args.vnc_host,
        capture_movement=args.capture_movement,
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
        remove_game_containers(game_name)
        logger.info(('Game cancelled.' % ()))
        raise
    if args.plot_realtime:
        plot_realtime.save(('%s/%s/frame_plot.png' % (args.game_dir,
                                                      game_name)))
    replay_files = set((glob.glob(
        ('%s/replays/%s_[0-7].rep' % (args.map_dir, game_name))) + glob.glob(
            ('%s/replays/%s_[0-7].REP' % (args.map_dir, game_name)))))
    for replay_file in replay_files:
        nth_player = int(replay_file[:(-4)].split('_')[(-1)])
        os.rename(replay_file, ('%s/%s/player_%s.rep' %
                                (args.game_dir, game_name, nth_player)))
    if is_1v1_game:
        game_time = (time.time() - time_start)
        game_result = GameResult(game_name, players, game_time,
                                 is_realtime_outed, args.map_dir,
                                 args.game_dir)
        info = launch_params.copy()
        info.update(
            dict(
                read_overwrite=args.read_overwrite,
                bots=args.bots,
                is_crashed=game_result.is_crashed,
                is_gametime_outed=game_result.is_gametime_outed,
                is_realtime_outed=game_result.is_realtime_outed,
                game_time=game_result.game_time,
                winner=None,
                loser=None,
                winner_race=None,
                loser_race=None))
        if game_result.is_valid:
            info.update(
                dict(
                    winner=game_result.winner_player.name,
                    loser=game_result.loser_player.name,
                    winner_race=game_result.winner_player.race.value,
                    loser_race=game_result.loser_player.race.value))
        logger.debug(info)
        with open(('%s/%s/result.json' % (args.game_dir, game_name)),
                  'w') as f:
            json.dump(info, f, cls=EnumEncoder)
        logger.info(('game %s recorded' % (game_name, )))
        return game_result
    return None


class EnumEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, enum.Enum):
            return obj.value
        return super(EnumEncoder, self).default(obj)
