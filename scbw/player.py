import argparse
import datetime
import enum
import glob
import json
import logging
import os.path
import re
from dateutil.parser import parse as parse_iso_date
from scbw.bwapi import supported_versions, versions_md5s
from scbw.error import PlayerException
from scbw.utils import md5_file
logger = logging.getLogger(__name__)
SC_BOT_DIR = os.path.abspath('bots')


class PlayerRace(enum.Enum):
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


class BotType(enum.Enum):
    AI_MODULE = 'dll'
    EXE = 'exe'
    JAVA = 'jar'
    JYTHON = 'jython'


class BotJsonMeta():
    name = None
    race = None
    botType = None
    description = None
    update = None
    botBinary = None
    bwapiDLL = None
    botProfileURL = None
    javaDebugPort = None
    javaOpts = None


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

    def __init__(self, bot_dir):
        self.bot_dir = bot_dir
        self._check_structure()
        self.meta = self._read_meta()
        self.name = self.meta.name
        self.race = self.meta.race
        self.bot_type = self.meta.botType
        self.bot_filename = self._find_bot_filename(self.meta.botType)
        self.bwapi_version = self._find_bwapi_version()

    def _read_meta(self):
        with open(('%s/bot.json' % (self.bot_dir, )), 'r') as f:
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
                'Too many files found as candidates for bot launcher, launcher searched for files %s'
                % (expr, )))
        else:
            raise Exception((
                'Cannot find bot binary, launcher searched for %s' % (expr, )))

    @property
    def bot_basefilename(self):
        return os.path.basename(self.bot_filename)

    @property
    def bwapi_dll_file(self):
        return ('%s/BWAPI.dll' % (self.bot_dir, ))

    @property
    def bot_json_file(self):
        return ('%s/bot.json' % (self.bot_dir, ))

    @property
    def ai_dir(self):
        return ('%s/AI' % (self.bot_dir, ))

    @property
    def read_dir(self):
        return ('%s/read' % (self.bot_dir, ))

    def _check_structure(self):
        if (not os.path.exists(('%s' % (self.bot_dir, )))):
            raise PlayerException(
                ('Bot cannot be found in %s' % (self.bot_dir, )))
        if (not os.path.exists(self.bot_json_file)):
            raise PlayerException(('Bot JSON config cannot be found in %s' %
                                   (self.bot_json_file, )))
        if (not os.path.exists(self.bwapi_dll_file)):
            raise PlayerException(
                ('BWAPI.dll cannot be found in %s' % (self.bwapi_dll_file, )))
        if (not os.path.exists(('%s' % (self.ai_dir, )))):
            raise PlayerException(
                ('AI folder cannot be found in %s' % (self.ai_dir, )))
        if (not os.path.exists(('%s' % (self.read_dir, )))):
            raise PlayerException(
                ('read folder cannot be found in %s' % (self.read_dir, )))

    @staticmethod
    def parse_meta(json_spec):
        meta = BotJsonMeta()
        meta.name = json_spec['name']
        meta.race = PlayerRace[json_spec['race'].upper()]
        bot_type = json_spec['botType']
        if ((bot_type == 'JAVA_JNI') or (bot_type == 'JAVA_MIRROR')):
            bot_type = 'JAVA'
        meta.botType = BotType[bot_type]
        meta.description = (json_spec['description']
                            if ('description' in json_spec) else None)
        meta.update = (parse_iso_date(json_spec['update'])
                       if ('update' in json_spec) else None)
        meta.botBinary = (json_spec['botBinary']
                          if ('botBinary' in json_spec) else None)
        meta.bwapiDLL = (json_spec['bwapiDLL']
                         if ('bwapiDLL' in json_spec) else None)
        meta.botProfileURL = (json_spec['botProfileURL']
                              if ('botProfileURL' in json_spec) else None)
        meta.javaDebugPort = (json_spec['javaDebugPort']
                              if ('javaDebugPort' in json_spec) else None)
        meta.javaOpts = (json_spec['javaOpts']
                         if ('javaOpts' in json_spec) else None)
        return meta

    def _find_bwapi_version(self):
        bwapi_md5_hash = md5_file(self.bwapi_dll_file)
        if (bwapi_md5_hash not in versions_md5s.values()):
            raise PlayerException(("""
                Bot uses unrecognized version of BWAPI, with md5 hash %s.
                Supported versions are: %s
                """ % (bwapi_md5_hash, ', '.join(supported_versions))))
        version = [
            version for (version, bwapi_hash) in versions_md5s.items()
            if (bwapi_hash == bwapi_md5_hash)
        ][0]
        if (version not in supported_versions):
            raise PlayerException(("""
                Bot uses unsupported version of BWAPI: %s.
                Supported versions are: %s
                """ % (version, ', '.join(supported_versions))))
        return version


_races = '|'.join([race.value for race in PlayerRace])
_expr = re.compile(
    (('^[a-zA-Z0-9_][a-zA-Z0-9_. -]{0,40}(\\:(' + _races) + '))?$'))


def bot_regex(bot):
    if (not _expr.match(bot)):
        raise argparse.ArgumentTypeError(
            ("Bot specification '%s' is not valid, should match %s" %
             (bot, _expr.pattern)))
    return bot


def check_bot_exists(bot, bot_dir):
    BotPlayer(('%s/%s' % (bot_dir, bot)))
