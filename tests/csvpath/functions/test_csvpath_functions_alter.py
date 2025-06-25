import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsAlter(unittest.TestCase):
    def test_function_alter_1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[3][
                @s = alter("the quick brown dog", "dog", "fox")
            ]"""
        )
        path.fast_forward()
        assert path.variables["s"] == "the quick brown fox"

    def test_function_alter_2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[3][
                @s = alter("the quick brown dog", none(), "fox")
            ]"""
        )
        path.fast_forward()
        assert path.variables["s"] == "the quick brown dog"

    def test_function_alter_3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[3][
                @s = alter("the quick brown dog quickly ran", "quick", "slow")
            ]"""
        )
        path.fast_forward()
        assert path.variables["s"] == "the slow brown dog slowly ran"

    def test_function_alter_4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[3][
                @s = alter("the quick brown dog", "fox", none())
            ]"""
        )
        path.fast_forward()
        assert path.variables["s"] == "the quick brown dog"
