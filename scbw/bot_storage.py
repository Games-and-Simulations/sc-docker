import json
import logging
import os
import shutil
from os.path import exists
from typing import Optional, Dict

import numpy as np
import requests

from .player import BotPlayer, BotJsonMeta
from .utils import levenshtein_dist, download_extract_zip, download_file

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

        logger.debug(f"found bot in {f_name}")
        bot = BotPlayer(name, self.bot_dir)

        return bot


class SscaitBotStorage(BotStorage):
    MAX_MATCHING_SUGGESTIONS = 5

    def __init__(self, bot_dir: str):
        self.bot_dir = bot_dir

    def find_bot(self, name: str) -> Optional[BotPlayer]:
        try:
            bots = self.get_bot_specs()
            bot_names = np.array([bot['name'] for bot in bots])
            matching_name = self.find_matching_name(name, bot_names)

            if not exists(f"{self.bot_dir}/{matching_name}"):
                json_spec = [bot for bot in bots if bot['name'] == matching_name][0]
                logger.debug(json_spec)

                bot_spec = self.try_download(json_spec)
                if bot_spec is None:
                    return None

                logger.info(f"Successfully downloaded {bot_spec.name} from SSCAIT server")

            return BotPlayer(matching_name, self.bot_dir)

        except Exception as e:
            logger.exception(e)
            logger.warning(f"Could not find the bot '{name}' on SSCAIT server")
            return None

    def find_matching_name(self, name: str, bot_names: np.ndarray):
        if name in bot_names:
            return name
        else:
            logger.info(f"Could not find {name}, trying to find closest match "
                        f"in {len(bot_names)} available bots")

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

    def try_download(self, json_spec: Dict) -> Optional[BotJsonMeta]:
        bot_spec = BotPlayer.parse_meta(json_spec)

        base_dir = f'{self.bot_dir}/{bot_spec.name}'
        try:
            os.makedirs(base_dir, exist_ok=False)

            # use http because local network on CTU has broken records
            # and it should work everywhere...
            download_extract_zip(bot_spec.botBinary.replace("https", "http"), f'{base_dir}/AI')
            download_file(bot_spec.bwapiDLL.replace("https", "http"), f'{base_dir}/BWAPI.dll')

            os.makedirs(f'{base_dir}/read', exist_ok=False)
            os.makedirs(f'{base_dir}/write', exist_ok=False)

            with open(f'{base_dir}/bot.json', 'w') as f:
                json.dump(json_spec, f)

            return bot_spec

        except Exception as e:
            logger.exception(f"Failed to process bot {bot_spec.name}")
            logger.exception(e)

            logger.info(f"Cleaning up dir {base_dir}")
            shutil.rmtree(base_dir)

            return None
