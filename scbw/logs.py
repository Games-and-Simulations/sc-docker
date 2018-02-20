import glob
from typing import List


def find_logs(log_dir: str, game_name: str) -> List[str]:
    return glob.glob(f"{log_dir}/{game_name}*.log")


def find_replays(map_dir: str, game_name: str) -> List[str]:
    return list(set(
        glob.glob(f"{map_dir}/replays/{game_name}_*.rep") +
        glob.glob(f"{map_dir}/replays/{game_name}_*.REP")
    ))


def find_results(log_dir: str, game_name: str) -> List[str]:
    return glob.glob(f"{log_dir}/{game_name}_*_results.json")


def find_frames(log_dir: str, game_name: str) -> List[str]:
    return glob.glob(f"{log_dir}/{game_name}_*_frames.csv")
