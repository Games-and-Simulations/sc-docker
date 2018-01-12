import argparse
import glob
import json
import logging
import re
from datetime import datetime
from enum import Enum
from os.path import exists, basename, abspath
from typing import Dict

from dateutil.parser import parse as parse_iso_date

logger = logging.getLogger(__name__)

SC_BOT_DIR = abspath("bots")


class PlayerRace(Enum):
    PROTOSS = 'P'
    ZERG = 'Z'
    TERRAN = 'T'
    RANDOM = 'R'


class Player:
    name = "noname"
    race = PlayerRace.RANDOM

    def __str__(self):
        return f"{self.__class__.__name__}:{self.name}:{self.race.value}"


class HumanPlayer(Player):
    name = "human"


class BotType(Enum):
    AI_MODULE = "dll"
    EXE = "exe"
    JAVA = "jar"


class BotJsonMeta:
    name: str = None
    race: PlayerRace = None
    description: str = None
    botType: BotType = None

    # last updated
    update: datetime = None

    # links to SSCAIT website
    botBinary: str = None
    bwapiDLL: str = None
    botProfileURL: str = None


class BotPlayer(Player):
    """
    Each bot has following structure in the bots directory:
    - bot.json        bot JSON config file
    - BWAPI.dll       BWAPI.dll to inject into game
    - AI/             bot binaries (as from SSCAIT).
                      In its root must be some executable - EXE, JAR, DLL
    - read/*          all read files that will be mounted

    At the time of creating instance it must have the file system structure satisfied.
    """

    def __init__(self, name: str, bot_dir: str = SC_BOT_DIR):
        self.name = name

        self.bot_dir = bot_dir
        self.base_dir = bot_dir + "/" + self.name

        self._check_structure()
        self.meta = self._read_meta()
        self.race = self.meta.race
        self.bot_type = self.meta.botType
        self.bot_filename = self._find_bot_filename(self.meta.botType)

    def _read_meta(self) -> BotJsonMeta:
        with open(f"{self.base_dir}/bot.json", "r") as f:
            json_spec = json.load(f)

        return self.parse_meta(json_spec)

    def _find_bot_filename(self, bot_type: BotType) -> str:
        expr = f"{self.ai_dir}/*.{bot_type.value}"
        candidate_files = [file for file in glob.glob(expr)
                           if "BWAPI" not in file]

        if len(candidate_files) == 1:
            return list(candidate_files)[0]
        elif len(candidate_files) > 1:
            raise Exception(f"Too many files found as candidates "
                            f"for bot launcher, searching for {expr}")
        else:
            raise Exception(f"Cannot find bot launcher, searching for {expr}")

    @property
    def bot_basefilename(self) -> str:
        return basename(self.bot_filename)

    @property
    def bwapi_dll_file(self):
        return f"{self.base_dir}/BWAPI.dll"

    @property
    def bot_json_file(self):
        return f"{self.base_dir}/bot.json"

    @property
    def ai_dir(self):
        return f"{self.base_dir}/AI"

    @property
    def read_dir(self):
        return f"{self.base_dir}/read"

    @property
    def write_dir(self):
        return f"{self.base_dir}/write"

    def _check_structure(self):
        if not exists(f"{self.base_dir}"):
            raise Exception(f"Bot cannot be found in {self.base_dir}")
        if not exists(self.bot_json_file):
            raise Exception(f"Bot JSON config cannot be found in {self.bot_json_file}")
        if not exists(self.bwapi_dll_file):
            raise Exception(f"BWAPI.dll cannot be found in {self.bwapi_dll_file}")
        if not exists(f"{self.ai_dir}"):
            raise Exception(f"AI folder cannot be found in {self.ai_dir}")
        if not exists(f"{self.read_dir}"):
            raise Exception(f"read folder cannot be found in {self.read_dir}")
        if not exists(f"{self.write_dir}"):
            raise Exception(f"write folder cannot be found in {self.write_dir}")

    @staticmethod
    def parse_meta(json_spec: Dict):
        meta = BotJsonMeta()
        meta.name = json_spec['name']
        meta.race = PlayerRace[json_spec['race'].upper()]
        meta.description = json_spec['description']

        bot_type = json_spec['botType']
        if bot_type == "JAVA_JNI" or bot_type == "JAVA_MIRROR":
            bot_type = "JAVA"
        meta.botType = BotType[bot_type]

        meta.update = parse_iso_date(json_spec['update'])
        meta.botBinary = json_spec['botBinary']
        meta.bwapiDLL = json_spec['bwapiDLL']
        meta.botProfileURL = json_spec['botProfileURL']

        return meta


_races = "|".join([race.value for race in PlayerRace])
_expr = re.compile("^[a-zA-Z0-9_][a-zA-Z0-9_. -]{0,40}"
                   "(\:(" + _races + "))?$")


def bot_regex(bot: str):
    if not _expr.match(bot):
        raise argparse.ArgumentTypeError(
            f"Bot specification '{bot}' is not valid, should match {_expr.pattern}")
    return bot
