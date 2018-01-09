from typing import List, Iterable

from player import Bot, PlayerRace, BWAPIVersion
from bot_storage import BotStorage


def retrieve_bots(bot_specs: Iterable[str],
                  bot_storages: Iterable[BotStorage]) -> List[Bot]:
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

    return bots
