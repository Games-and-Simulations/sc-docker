import argparse
import glob
import json
import logging
import re
from datetime import datetime
from enum import Enum
from os.path import exists, basename, abspath
from dateutil.parser import parse as parse_iso_date
logger = logging.getLogger(__name__)
SC_BOT_DIR = abspath('bots')


class PlayerRace(Enum):
    PROTOSS = 'P'
    ZERG = 'Z'
    TERRAN = 'T'
    RANDOM = 'R'


class Player():
    name = 'noname'
    race = PlayerRace.RANDOM

    def __str__(self):
        return ('%s:%s:%s' % (self.__class__.__name__, self.name,
                              self.race.value))


class HumanPlayer(Player):
    name = 'human'


class BotType(Enum):
    AI_MODULE = 'dll'
    EXE = 'exe'
    JAVA = 'jar'


class BotJsonMeta():
    name = None
    race = None
    description = None
    botType = None
    update = None
    botBinary = None
    bwapiDLL = None
    botProfileURL = None


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

    def __init__(self, name, bot_dir=SC_BOT_DIR):
        self.name = name
        self.bot_dir = bot_dir
        self.base_dir = ((bot_dir + '/') + self.name)
        self._check_structure()
        self.meta = self._read_meta()
        self.race = self.meta.race
        self.bot_type = self.meta.botType
        self.bot_filename = self._find_bot_filename(self.meta.botType)

    def _read_meta(self):
        with open(('%s/bot.json' % (self.base_dir, )), 'r') as f:
            json_spec = json.load(f)
        return self.parse_meta(json_spec)

    def _find_bot_filename(self, bot_type):
        expr = ('%s/*.%s' % (self.ai_dir, bot_type.value))
        candidate_files = [
            file for file in glob.glob(expr) if ('BWAPI' not in file)
        ]
        if (len(candidate_files) == 1):
            return list(candidate_files)[0]
        elif (len(candidate_files) > 1):
            raise Exception((
                'Too many files found as candidates for bot launcher, searching for %s'
                % (expr, )))
        else:
            raise Exception(
                ('Cannot find bot launcher, searching for %s' % (expr, )))

    @property
    def bot_basefilename(self):
        return basename(self.bot_filename)

    @property
    def bwapi_dll_file(self):
        return ('%s/BWAPI.dll' % (self.base_dir, ))

    @property
    def bot_json_file(self):
        return ('%s/bot.json' % (self.base_dir, ))

    @property
    def ai_dir(self):
        return ('%s/AI' % (self.base_dir, ))

    @property
    def read_dir(self):
        return ('%s/read' % (self.base_dir, ))

    @property
    def write_dir(self):
        return ('%s/write' % (self.base_dir, ))

    def _check_structure(self):
        if (not exists(('%s' % (self.base_dir, )))):
            raise Exception(('Bot cannot be found in %s' % (self.base_dir, )))
        if (not exists(self.bot_json_file)):
            raise Exception(('Bot JSON config cannot be found in %s' %
                             (self.bot_json_file, )))
        if (not exists(self.bwapi_dll_file)):
            raise Exception(
                ('BWAPI.dll cannot be found in %s' % (self.bwapi_dll_file, )))
        if (not exists(('%s' % (self.ai_dir, )))):
            raise Exception(
                ('AI folder cannot be found in %s' % (self.ai_dir, )))
        if (not exists(('%s' % (self.read_dir, )))):
            raise Exception(
                ('read folder cannot be found in %s' % (self.read_dir, )))
        if (not exists(('%s' % (self.write_dir, )))):
            raise Exception(
                ('write folder cannot be found in %s' % (self.write_dir, )))

    @staticmethod
    def parse_meta(json_spec):
        meta = BotJsonMeta()
        meta.name = json_spec['name']
        meta.race = PlayerRace[json_spec['race'].upper()]
        meta.description = json_spec['description']
        bot_type = json_spec['botType']
        if ((bot_type == 'JAVA_JNI') or (bot_type == 'JAVA_MIRROR')):
            bot_type = 'JAVA'
        meta.botType = BotType[bot_type]
        meta.update = parse_iso_date(json_spec['update'])
        meta.botBinary = json_spec['botBinary']
        meta.bwapiDLL = json_spec['bwapiDLL']
        meta.botProfileURL = json_spec['botProfileURL']
        return meta


_races = '|'.join([race.value for race in PlayerRace])
_expr = re.compile(
    (('^[a-zA-Z0-9_][a-zA-Z0-9_. -]{0,40}(\\:(' + _races) + '))?$'))


def bot_regex(bot):
    if (not _expr.match(bot)):
        raise argparse.ArgumentTypeError(
            ("Bot specification '%s' is not valid, should match %s" %
             (bot, _expr.pattern)))
    return bot
