import unittest
from .files_test import TestFindFiles

def suite():

    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestFindFiles))

    return suite