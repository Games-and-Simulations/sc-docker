import glob
from typing import List


def find_logs(game_dir: str, game_name: str) -> List[str]:
    return glob.glob(f"{game_dir}/{game_name}/logs_*/*.log")


def find_replays(game_dir: str, game_name: str) -> List[str]:
    return list(set(
        glob.glob(f"{game_dir}/{game_name}/*.rep")
    ))


def find_scores(game_dir: str, game_name: str) -> List[str]:
    return glob.glob(f"{game_dir}/{game_name}/logs_*/scores.json")


def find_frames(game_dir: str, game_name: str) -> List[str]:
    return glob.glob(f"{game_dir}/{game_name}/logs_*/frames.csv")

def find_unit_events(game_dir: str, game_name: str) -> List[str]:
    return glob.glob(f"{game_dir}/{game_name}/logs_*/unit_events.csv")
