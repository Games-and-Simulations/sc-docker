import glob
from typing import List


def find_logs(log_dir: str, game_name: str) -> List[str]:
    return glob.glob(f"{log_dir}/{game_name}*.log")
