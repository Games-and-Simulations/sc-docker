import os
import unittest
from scbw.logs import find_logs

class TestFindFiles(unittest.TestCase):
    root_dir = os.path.dirname(__file__)

    def test_logs(self):
        test_files_dir = os.path.normpath(self.root_dir + "/data/logs_similar_names")
        logs = find_logs(test_files_dir, "GAME_test")
        self.assertEqual(4, len(logs), "Only 4 log files should be found")

if __name__ == '__main__':
    unittest.main()