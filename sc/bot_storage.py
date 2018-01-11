import json
import logging
from os.path import exists
from pprint import pprint
from typing import Optional

import numpy as np
import requests

from player import BotPlayer
from utils import levenshtein_dist

logger = logging.getLogger(__name__)


class BotStorage:
    def find_bot(self, name: str) -> Optional[BotPlayer]:
        raise NotImplemented


class LocalBotStorage(BotStorage):
    def __init__(self, bot_dir: str):
        self.bot_dir = bot_dir

    def find_bot(self, name: str) -> Optional[BotPlayer]:
        f_name = f"{self.bot_dir}/{name}"
        logger.debug(f"checking bot in {f_name}")
        if not exists(f_name):
            return None

        logger.info(f"found bot in {f_name}")
        bot = BotPlayer(name, self.bot_dir)

        return bot


class SscaitBotStorage(BotStorage):
    MAX_MATCHING_SUGGESTIONS = 5

    def find_bot(self, name: str) -> Optional[BotPlayer]:
        try:
            bots = self.get_bot_specs()
            bot_names = np.array([bot['name'] for bot in bots])
            matching_name = self.find_matching_name(name, bot_names)

            bot_spec = [bot for bot in bots if bot['name'] == matching_name][0]

            # todo: finish try_download
            logger.info("not finished yet")
            pprint(bot_spec)

            return BotPlayer(bot_spec['name'])
        except Exception as e:
            logger.exception(e)
            logger.warning(f"Could not find the bot '{name}' on SSCAIT server")
            return None

    def find_matching_name(self, name: str, bot_names: np.ndarray):
        if name in bot_names:
            return name
        else:
            logger.info(f"Could not find {name}, trying to find closest match")

            distances = np.array([levenshtein_dist(name, bot_name) for bot_name in bot_names])
            closest_idxs = np.argsort(distances)[:self.MAX_MATCHING_SUGGESTIONS]
            closest_matching = bot_names[closest_idxs]

            logger.info(f"Found these bots: ")
            for i, closest_bot in enumerate(closest_matching):
                logger.info(f"{i}: {closest_bot}")

            logger.info(
                f"Which would you like to use? (enter number 0-{self.MAX_MATCHING_SUGGESTIONS-1})")
            bot_idx = max(min(self.MAX_MATCHING_SUGGESTIONS - 1, int(input())), 0)
            return closest_matching[bot_idx]

    def get_bot_specs(self):
        response = requests.get("http://sscaitournament.com/api/bots.php")
        return json.loads(response.content)
