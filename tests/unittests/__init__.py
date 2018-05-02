import unittest
from .files_test import TestFindFiles
from .meta_test import TestBotMetaParsing

def suite():

    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestFindFiles))
    suite.addTest(unittest.makeSuite(TestBotMetaParsing))

    return suite