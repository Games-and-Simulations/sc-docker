import os
import json
import unittest
from scbw.player import BotPlayer, PlayerRace, BotType

class TestBotMetaParsing(unittest.TestCase):
    root_dir = os.path.dirname(__file__)

    def test_parse_exe_bot(self):       
        bot_filename = os.path.normpath(self.root_dir + "/data/bots/regular/bot.json")
        with open(bot_filename, "r") as f:
            bot_json = json.load(f)
        bot_meta = BotPlayer.parse_meta(bot_json)
        
        self.assertEqual("AKBot_FAP", bot_meta.name)
        self.assertEqual(PlayerRace.RANDOM, bot_meta.race)
        self.assertEqual(BotType.EXE, bot_meta.botType)
        self.assertEqual("Rule-based bot\nhttps://github.com/kant2002/ualbertabot\n=======================\nWorking on having good performance in playing games first.", bot_meta.description)
        self.assertEqual("https://sscaitournament.com/bot_binary.php?bot=Andrey+Kurdiumov&bwapi_dll=true", bot_meta.bwapiDLL)
        self.assertEqual("https://sscaitournament.com/index.php?action=botDetails&bot=Andrey+Kurdiumov", bot_meta.botProfileURL)
        self.assertIsNone(bot_meta.javaDebugPort)

    def test_parse_java_bot(self):       
        bot_filename = os.path.normpath(self.root_dir + "/data/bots/javabot/bot.json")
        with open(bot_filename, "r") as f:
            bot_json = json.load(f)
        bot_meta = BotPlayer.parse_meta(bot_json)
        
        self.assertEqual("PurpleWave", bot_meta.name)
        self.assertEqual(PlayerRace.PROTOSS, bot_meta.race)
        self.assertEqual(BotType.JAVA, bot_meta.botType)
        self.assertEqual(u'Disabled till end of tourney since being an extra<br/>-----<br/>PurpleWave will be back after the tournament. Go 🍒\u03c0! :)\n<br><br>\nBuilt with love. https://github.com/dgant/PurpleWave\n', bot_meta.description)
        self.assertEqual("https://sscaitournament.com/bot_binary.php?bot=PurpleWave&bwapi_dll=true", bot_meta.bwapiDLL)
        self.assertEqual("https://sscaitournament.com/index.php?action=botDetails&bot=PurpleWave", bot_meta.botProfileURL)
        self.assertEqual(1, bot_meta.javaDebugPort)
        self.assertEqual("--Xmx2048m", bot_meta.javaOpts)

if __name__ == '__main__':
    unittest.main()