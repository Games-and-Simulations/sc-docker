import json
import logging
import os
import os.path
import shutil
import numpy as np
import requests
from scbw.player import BotPlayer, BotJsonMeta
from scbw.utils import levenshtein_dist, download_extract_zip, download_file
logger = logging.getLogger(__name__)


class BotStorage():
    def find_bot(self, name):
        raise NotImplemented


class LocalBotStorage(BotStorage):
    def __init__(self, bot_dir):
        self.bot_dir = bot_dir

    def find_bot(self, name):
        f_name = ('%s/%s' % (self.bot_dir, name))
        logger.debug(('checking bot in %s' % (f_name, )))
        if (not os.path.exists(f_name)):
            return None
        logger.debug(('found bot in %s' % (f_name, )))
        bot = BotPlayer(f_name)
        return bot


class SscaitBotStorage(BotStorage):
    MAX_MATCHING_SUGGESTIONS = 5

    def __init__(self, bot_dir):
        self.bot_dir = bot_dir

    def find_bot(self, name):
        try:
            bots = self.get_bot_specs()
            bot_names = np.array([bot['name'] for bot in bots])
            matching_name = self.find_matching_name(name, bot_names)
            if (not os.path.exists(('%s/%s' % (self.bot_dir, matching_name)))):
                json_spec = [
                    bot for bot in bots if (bot['name'] == matching_name)
                ][0]
                logger.debug(json_spec)
                bot_spec = self.try_download(json_spec)
                if (bot_spec is None):
                    return None
                logger.info(('Successfully downloaded %s from SSCAIT server' %
                             (bot_spec.name, )))
            return BotPlayer(('%s/%s' % (self.bot_dir, matching_name)))
        except Exception as e:
            logger.exception(e)
            logger.warning(
                ("Could not find the bot '%s' on SSCAIT server" % (name, )))
            return None

    def find_matching_name(self, name, bot_names):
        if (name in bot_names):
            return name
        else:
            logger.info((
                'Could not find %s, trying to find closest match in %s available bots'
                % (name, len(bot_names))))
            distances = np.array(
                [levenshtein_dist(name, bot_name) for bot_name in bot_names])
            closest_idxs = np.argsort(distances)[:
                                                 self.MAX_MATCHING_SUGGESTIONS]
            closest_matching = bot_names[closest_idxs]
            logger.info(('Found these bots: ' % ()))
            for (i, closest_bot) in enumerate(closest_matching):
                logger.info(('%s: %s' % (i, closest_bot)))
            logger.info(('Which would you like to use? (enter number 0-%s)' % (
                (self.MAX_MATCHING_SUGGESTIONS - 1), )))
            bot_idx = max(
                min((self.MAX_MATCHING_SUGGESTIONS - 1), int(input())), 0)
            return closest_matching[bot_idx]

    def get_bot_specs(self):
        return requests.get('http://sscaitournament.com/api/bots.php').json()

    def try_download(self, json_spec):
        bot_spec = BotPlayer.parse_meta(json_spec)
        base_dir = ('%s/%s' % (self.bot_dir, bot_spec.name))
        try:
            os.makedirs(base_dir, exist_ok=False)
            download_extract_zip(
                bot_spec.botBinary.replace('https', 'http'),
                ('%s/AI' % (base_dir, )))
            download_file(
                bot_spec.bwapiDLL.replace('https', 'http'),
                ('%s/BWAPI.dll' % (base_dir, )))
            os.makedirs(('%s/read' % (base_dir, )), exist_ok=False)
            os.makedirs(('%s/write' % (base_dir, )), exist_ok=False)
            with open(('%s/bot.json' % (base_dir, )), 'w') as f:
                json.dump(json_spec, f)
            return bot_spec
        except Exception as e:
            logger.exception(('Failed to process bot %s' % (bot_spec.name, )))
            logger.exception(e)
            logger.info(('Cleaning up dir %s' % (base_dir, )))
            shutil.rmtree(base_dir)
            return None
