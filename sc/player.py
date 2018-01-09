import argparse
import logging
import os
import pickle
import re
from enum import Enum
from os.path import exists, basename

from bwapi import BWAPIVersion

logger = logging.getLogger(__name__)


class PlayerRace(Enum):
    PROTOSS = 'P'
    ZERG = 'Z'
    TERRAN = 'T'
    RANDOM = 'R'


class Player:
    name = "noname"
    race = PlayerRace.RANDOM


class HumanPlayer(Player):
    name = "human"

    def __str__(self):
        return f"{self.name}:{self.race.value}"


class BotType(Enum):
    AI_MODULE = "dll"
    EXE = "exe"
    JAVA_MIRROR = "jar"


class BotPlayer(Player):
    def __init__(self,
                 name: str,
                 bot_filename: str,
                 bot_type: BotType):
        self.name = name
        self.bot_type = bot_type
        self.bot_filename = bot_filename

        self.race: PlayerRace = None
        self.bwapi_version: BWAPIVersion = None

    def can_launch(self):
        return exists(self.bot_filename) \
               and self.race is not None \
               and self.bwapi_version is not None

    def has_settings(self):
        return exists(self.settings_file)

    def save_settings(self):
        with open(self.settings_file, "wb") as f:
            pickle.dump((self.race, self.bwapi_version), f)

    def load_settings(self):
        with open(self.settings_file, "rb") as f:
            self.race, self.bwapi_version = pickle.load(f)

    @property
    def settings_file(self):
        return os.path.splitext(self.bot_filename)[0] + ".pickle"

    @property
    def bot_basefilename(self) -> str:
        return basename(self.bot_filename)

    def __str__(self):
        return f"{self.name}:{self.race.value}:{self.bwapi_version.value}"


_races = "|".join([race.value for race in PlayerRace])
_bwapis = "|".join([bwapi.value for bwapi in BWAPIVersion])
_expr = re.compile("^[a-zA-Z0-9_][a-zA-Z0-9_\\- ]{0,15}"
                   "((\:(" + _races + "))?(\:(" + _bwapis + "))?|(\:\:(" + _bwapis + ")))$")


def bot_regex(bot: str):
    if not _expr.match(bot):
        raise argparse.ArgumentTypeError(f"Bot specification '{bot}' is not valid, "
                                         "maybe you forgot to set the race?")
    return bot
