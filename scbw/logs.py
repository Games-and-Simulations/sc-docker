import glob


def find_logs(game_dir, game_name):
    return glob.glob(('%s/%s/logs_*/*.log' % (game_dir, game_name)))


def find_replays(game_dir, game_name):
    return list(set(glob.glob(('%s/%s/*.rep' % (game_dir, game_name)))))


def find_scores(game_dir, game_name):
    return glob.glob(('%s/%s/logs_*/scores.json' % (game_dir, game_name)))


def find_frames(game_dir, game_name):
    return glob.glob(('%s/%s/logs_*/frames.csv' % (game_dir, game_name)))
