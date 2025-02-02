import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.util.config import Config
from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.util.exceptions import ChildrenException

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"
NUMBERS = f"tests{os.sep}test_resources{os.sep}numbers3.csv"


class TestValidBasicTypesInteger(unittest.TestCase):
    def test_function_integer4(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(
            f"""
                ~ return-mode: matches
                  validation-mode: no-raise, no-stop ~
                ${NUMBERS}[1*] [
                        integer(#1)
                        integer(#2)
                ]"""
        )
        lines = path.collect()
        # the int, None pair is acceptable because not notnone
        assert len(lines) == 6

    def test_function_integer5(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(
            f"""
                ~ return-mode: matches
                  validation-mode: no-raise, no-stop ~
                ${NUMBERS}[6] [
                        integer(#1)
                        integer(#2)
                ]"""
        )
        lines = path.collect()
        assert len(lines) == 0
