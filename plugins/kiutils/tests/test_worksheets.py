"""Unittests of worksheet related classes

Authors:
    (C) Marvin Mager - @mvnmgrx - 2022

License identifier:
    GPL-3.0
"""

import unittest
from os import path

from kiutils.wks import WorkSheet
from tests.testfunctions import (
    TEST_BASE,
    prepare_test,
    to_file_and_compare,
)

WORKSHEET_BASE = path.join(TEST_BASE, "worksheets")


class Tests_WorkSheets(unittest.TestCase):
    """Test cases for Worksheets"""

    def setUp(self) -> None:
        prepare_test(self)
        return super().setUp()

    def test_allWorkSheetItems(self):
        """Tests the parsing of all available worksheet items"""
        self.testData.compareToTestFile = True
        self.testData.pathToTestFile = path.join(
            WORKSHEET_BASE, "test_allWorkSheetItems"
        )
        wks = WorkSheet().from_file(self.testData.pathToTestFile)
        self.assertTrue(to_file_and_compare(wks, self.testData))

    def test_createNewWorksheet(self):
        """Tests the ``create_new()`` function to create a new empty worksheet"""
        self.testData.compareToTestFile = True
        self.testData.pathToTestFile = path.join(
            WORKSHEET_BASE, "test_createNewWorksheet"
        )
        wks = WorkSheet.create_new()
        self.assertTrue(to_file_and_compare(wks, self.testData))
