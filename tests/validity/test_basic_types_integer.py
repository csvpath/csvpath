import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.util.config import Config
from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.util.exceptions import ChildrenException

PATH = "tests/test_resources/test.csv"
NUMBERS = "tests/test_resources/numbers3.csv"


class TestValidBasicTypesInteger(unittest.TestCase):
    def test_function_integer4(self):
        path = CsvPath()
        path.parse(
            f"""
                ~ return-mode: matches
                  validation-mode: no-raise, no-stop ~
                ${NUMBERS}[1*] [
                        integer(1)
                        integer(2)
                ]"""
        )
        lines = path.collect()
        assert len(lines) == 5

    def test_function_integer5(self):
        path = CsvPath()
        path.parse(
            f"""
                ~ return-mode: matches
                  validation-mode: no-raise, no-stop ~
                ${NUMBERS}[6] [
                        integer(1)
                        integer(2)
                ]"""
        )
        lines = path.collect()
        assert len(lines) == 0
