import json
import logging
from typing import List, Optional

from scbw.logs import find_frames, find_unit_events, find_logs, find_replays, find_scores
from scbw.player import Player

logger = logging.getLogger(__name__)


class ScoreResult:
    def __init__(
            self,
            is_winner: bool,
            is_crashed: bool,
            timed_out: bool,
            building_score: int,
            kill_score: int,
            razing_score: int,
            unit_score: int,
    ) -> None:
        self.is_winner = is_winner
        self.is_crashed = is_crashed
        self.timed_out = timed_out
        self.building_score = building_score
        self.kill_score = kill_score
        self.razing_score = razing_score
        self.unit_score = unit_score

    @staticmethod
    def load_score(score_file: str) -> 'ScoreResult':
        with open(score_file, "r") as f:
            v = json.load(f)

        return ScoreResult(
            v['is_winner'],
            v['is_crashed'],
            v['timed_out'],
            v['building_score'],
            v['kill_score'],
            v['razing_score'],
            v['unit_score'],
        )


class GameResult:
    def __init__(
            self,
            game_name: str,
            players: List[Player],
            game_time: float,
            is_realtime_outed: bool,
            map_dir: str,
            game_dir: str
    ) -> None:
        self.game_name = game_name
        self.game_time = game_time
        self.players = players

        self.map_dir = map_dir
        self.game_dir = game_dir

        self._is_crashed = None
        self._is_gametime_outed = None
        self.is_realtime_outed = is_realtime_outed

        self._winner_player = None
        self._nth_winner_player = None
        self._loser_player = None
        self._nth_loser_player = None

        self._log_files = None
        self._replay_files = None
        self._frame_files = None
        self._unit_event_files = None
        self._score_files = None

        self.score_results = []

        self._is_processed = False

    def _process_files(self) -> None:
        # this whole processing assumes 1v1 bot vs bot games
        if self._is_processed:
            return

        self._is_processed = True

        if self.is_realtime_outed:
            return

        num_players = len(self.players)

        if len(self.score_files) != num_players:
            logger.warning(f"Not all score files have been recorded for game '{self.game_name}'")
            logger.warning(f"Expected {num_players} score files, got {len(self.score_files)}")
            logger.warning("Assuming a crash happened.")
            self._is_crashed = True
            return

        scores = {score_file: ScoreResult.load_score(score_file)
                   for score_file in sorted(self.score_files)}
        if any(score.is_crashed for score in scores.values()):
            logger.warning(f"Some of the players crashed in game '{self.game_name}'")
            self._is_crashed = True
            return

        if any(score.timed_out for score in scores.values()):
            logger.warning(f"Some of the players timed out in game '{self.game_name}'")
            self._is_gametime_outed = True
            return

        if not any(score.is_winner for score in scores.values()):
            logger.warning(f"No winner found in game '{self.game_name}'")
            logger.warning("Assuming a crash happened.")
            self._is_crashed = True
            return

        if sum(int(score.is_winner) for score in scores.values()) > 1:
            logger.warning(f"There are multiple winners of a game '{self.game_name}'")
            logger.warning("This can indicates possible game result corruption!")
            logger.warning("Assuming a crash happened.")
            self._is_crashed = True
            return

        winner_score_file = [file for file, score in scores.items() if score.is_winner][0]
        nth_player = int(winner_score_file.replace("/scores.json", "").replace("\\scores.json", "").split("_")[-1])

        self._nth_winner_player = nth_player
        self._nth_loser_player = 1 - nth_player
        self._winner_player = self.players[self._nth_winner_player]
        self._loser_player = self.players[self._nth_loser_player]
        self._is_crashed = False
        # todo: implement, maybe according to SSCAIT rules?
        self._is_gametime_outed = False
        self.score_results = scores

    @property
    def replay_files(self) -> List[str]:
        if self._replay_files is None:
            self._replay_files = find_replays(self.game_dir, self.game_name)
        return self._replay_files

    @property
    def log_files(self) -> List[str]:
        if self._log_files is None:
            self._log_files = find_logs(self.game_dir, self.game_name)
        return self._log_files

    @property
    def frame_files(self) -> List[str]:
        if self._frame_files is None:
            self._frame_files = find_frames(self.game_dir, self.game_name)
        return self._frame_files

    @property
    def unit_event_files(self) -> List[str]:
        if self._unit_event_files is None:
            self._unit_event_files = find_unit_events(self.game_dir, self.game_name)
        return self._unit_event_files


    @property
    def score_files(self) -> List[str]:
        if self._score_files is None:
            self._score_files = find_scores(self.game_dir, self.game_name)
        return self._score_files

    # Bunch of getters
    @property
    def is_valid(self) -> bool:
        self._process_files()
        return not self.is_crashed and \
               not self.is_gametime_outed and \
               not self.is_realtime_outed

    @property
    def is_crashed(self) -> bool:
        self._process_files()
        return self._is_crashed

    @property
    def is_gametime_outed(self) -> bool:
        self._process_files()
        return self._is_gametime_outed

    @property
    def winner_player(self) -> Optional[Player]:
        self._process_files()
        return self._winner_player

    @property
    def nth_winner_player(self) -> Optional[int]:
        self._process_files()
        return self._nth_winner_player

    @property
    def loser_player(self) -> Optional[Player]:
        self._process_files()
        return self._loser_player

    @property
    def nth_loser_player(self) -> Optional[int]:
        self._process_files()
        return self._nth_loser_player
