from collections import Counter
from typing import List, Iterable

from bot_storage import BotStorage
from player import BotPlayer, PlayerRace, BWAPIVersion


def retrieve_bots(bot_specs: Iterable[str],
                  bot_storages: Iterable[BotStorage]) -> List[BotPlayer]:
    bots = []
    for bot_spec in bot_specs:
        parts = bot_spec.split(":")
        bot_name = parts[0]

        bot = None
        for bot_storage in bot_storages:
            maybe_bot = bot_storage.find_bot(bot_name)
            if maybe_bot:
                bot = maybe_bot
                break

        if bot is None:
            raise Exception(f"Could not find bot {bot_name}")

        # load settings before override
        if bot.has_settings():
            bot.load_settings()

        if len(parts) >= 2 and parts[1]:
            bot.race = PlayerRace(parts[1])
        if len(parts) >= 3 and parts[2]:
            bot.bwapi_version = BWAPIVersion(parts[2])

        if not bot.can_launch():
            raise Exception(f"Bot is not ready to launch!")

        bots.append(bot)

    # Make sure that the same bot doesn't play against itself (names should be unique)
    # This is to prevent overwriting and corrupting its own data in mounted dirs
    counter = Counter([bot.name for bot in bots])
    # todo: maybe automatic copy?
    for bot_name in counter.keys():
        if counter[bot_name] > 1:
            raise Exception(f"Bots with same names cannot play against themselves. "
                            f"Please create a copy of '{bot_name}' in the bot_dir "
                            f"with a different name (like '{bot_name}_copy') "
                            f"and start a game under this new reference name.")
    return bots
