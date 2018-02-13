import json
import logging
from typing import List

from .error import GameException
from .player import HumanPlayer, Player

logger = logging.getLogger(__name__)


class RawResult:
    def __init__(self,
                 is_winner: bool,
                 is_crashed: bool,
                 building_score: int,
                 kill_score: int,
                 razing_score: int,
                 unit_score: int,
                 ):
        self.is_winner = is_winner
        self.is_crashed = is_crashed
        self.building_score = building_score
        self.kill_score = kill_score
        self.razing_score = razing_score
        self.unit_score = unit_score

    @staticmethod
    def load_result(result_file: str):
        with open(result_file, "r") as f:
            v = json.load(f)

        return RawResult(
            v['is_winner'],
            v['is_crashed'],
            v['building_score'],
            v['kill_score'],
            v['razing_score'],
            v['unit_score'],
        )


class GameResult:
    def __init__(self,
                 game_name: str, players: List[Player],
                 game_time: float,

                 is_realtime_outed: bool,

                 replay_files: List[str], log_files: List[str],
                 frame_files: List[str], result_files: List[str]):
        self.game_name = game_name
        self.game_time = game_time
        self.players = players

        self.replay_files = replay_files
        self.log_files = log_files
        self.frame_files = frame_files
        self.result_files = result_files

        self.is_realtime_outed = is_realtime_outed

        self._is_crashed = None
        self._is_gametime_outed = None
        self._winner_player = None
        self._nth_winner_player = None
        self._loser_player = None
        self._nth_loser_player = None

        self._is_processed = False

    def _process_files(self):
        # todo: this is still written assuming one human player only
        # todo: and assumes 1v1 game
        if self._is_processed:
            return

        self._is_processed = True

        if self.is_realtime_outed:
            return

        num_players = len(self.players)
        num_human = sum(isinstance(player, HumanPlayer) for player in self.players)

        # human games do not log results (they do not use tournament module)
        if len(self.result_files) != num_players - num_human:
            logger.warning(f"Not all result files have been recorded for game '{self.game_name}'")
            logger.warning(f"Expected {num_players - num_human} result files, "
                           f"got {len(self.result_files)}")
            logger.warning("Assuming a crash happened.")
            self._is_crashed = True
            return

        results = {result_file: RawResult.load_result(result_file) for result_file in self.result_files}
        if any(result.is_crashed for result in results.values()):
            logger.warning(f"Some of the players crashed in game '{self.game_name}'")
            self._is_crashed = True
            return

        if not any(result.is_winner for result in results.values()):
            logger.warning(f"No winner found in game '{self.game_name}'")
            logger.warning("Assuming a crash happened.")
            self._is_crashed = True
            return

        if sum(int(result.is_winner) for result in results.values()) > 1:
            logger.warning(f"There are multiple winners of a game '{self.game_name}'")
            logger.warning("This can indicates possible game result corruption!")
            logger.warning("Assuming a crash happened.")
            self._is_crashed = True
            return

        winner_result_file = [file for file, result in results.items() if result.is_winner][0]
        nth_player = int(winner_result_file.replace("_results.json", "").split("_")[-1])

        self._nth_winner_player = nth_player
        self._nth_loser_player = 1-nth_player
        self._winner_player = self.players[self._nth_winner_player]
        self._loser_player = self.players[self._nth_loser_player]
        self._is_crashed = False
        # todo: implement, maybe according to SSCAIT rules?
        self._is_gametime_outed = False

    # Bunch of getters
    @property
    def is_valid(self):
        self._process_files()
        return not self.is_crashed and \
               not self.is_gametime_outed and \
               not self.is_realtime_outed

    @property
    def winner_player(self):
        self._process_files()
        return self._winner_player

    @property
    def is_crashed(self):
        self._process_files()
        return self._is_crashed

    @property
    def is_gametime_outed(self):
        self._process_files()
        return self._is_gametime_outed

    @property
    def winner_player(self):
        self._process_files()
        return self._winner_player

    @property
    def nth_winner_player(self):
        self._process_files()
        return self._nth_winner_player

    @property
    def loser_player(self):
        self._process_files()
        return self._loser_player

    @property
    def nth_loser_player(self):
        self._process_files()
        return self._nth_loser_player
