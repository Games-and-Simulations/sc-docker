import json


class Result:
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

        return Result(
            v['winner_player'] == 1,
            v['crashed'] == 1,
            v['building_score'],
            v['kill_score'],
            v['razing_score'],
            v['unit_score'],
        )
