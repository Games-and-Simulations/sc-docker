import glob
import os
from enum import Enum

import numpy as np


class GameType(Enum):
    TOP_VS_BOTTOM = "TOP_VS_BOTTOM"
    MELEE = "MELEE"
    FREE_FOR_ALL = "FREE_FOR_ALL"
    ONE_ON_ONE = "ONE_ON_ONE"
    USE_MAP_SETTINGS = "USE_MAP_SETTINGS"
    CAPTURE_THE_FLAG = "CAPTURE_THE_FLAG"
    GREED = "GREED"
    SLAUGHTER = "SLAUGHTER"
    SUDDEN_DEATH = "SUDDEN_DEATH"
    TEAM_MELEE = "TEAM_MELEE"
    TEAM_FREE_FOR_ALL = "TEAM_FREE_FOR_ALL"
    TEAM_CAPTURE_THE_FLAG = "TEAM_CAPTURE_THE_FLAG"


def find_winner(game_name: str, map_dir: str) -> int:
    replay_files = glob.glob(f"{map_dir}/replays/*-*-*_{game_name}_*.rep")
    replay_sizes = map(os.path.getsize, replay_files)

    winner_idx = np.argmax(replay_sizes)
    winner_file = replay_files[winner_idx]
    nth_player = winner_file.replace(".rep", "").split("_")[-1]
    return int(nth_player)
