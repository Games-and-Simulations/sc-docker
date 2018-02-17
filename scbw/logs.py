import glob


def find_logs(log_dir, game_name):
    return glob.glob(('%s/%s*.log' % (log_dir, game_name)))


def find_replays(map_dir, game_name):
    return (glob.glob(
        ('%s/replays/%s_*.rep' % (map_dir, game_name))) + glob.glob(
            ('%s/replays/%s_*.REP' % (map_dir, game_name))))


def find_results(log_dir, game_name):
    return glob.glob(('%s/%s_*_results.json' % (log_dir, game_name)))


def find_frames(log_dir, game_name):
    return glob.glob(('%s/%s_*_frames.csv' % (log_dir, game_name)))
