import glob


def find_logs(log_dir, game_name):
    return glob.glob(('%s/%s*.log' % (log_dir, game_name)))
