import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.util.config import Config
from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.util.exceptions import ChildrenException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
NUMBERS = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}numbers3.csv"
NUMBERS5 = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}numbers5.csv"


class TestCsvPathValidityValidBasicTypesDecimal(unittest.TestCase):
    def test_function_decimal1(self):
        path = CsvPath().parse(
            f""" ${NUMBERS}[*] [
                @st = decimal("abc")
            ] """
        )
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.collect()

    def test_function_decimal2(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f""" ~ validation-mode:no-raise ~
                ${NUMBERS}[1] [
                ~ too high 3.52 ~
                push("a", decimal.one(#numbers31, 1, 1) )
                ~ too high 3.52 ~
                push("a", decimal.two(#0, 1, 0) )
                ~ fits 3.52 ~
                push("a", decimal.three(#numbers31, 20) )
                ~ fits 3.52 ~
                push("a", decimal.four(#0, 20, 2) )
                ~ too low 3.52 ~
                push("a", decimal.five(#numbers31, none(), 18.60) )
                ~ too high 3.52 ~
                push("a", decimal.six(#0, -1, -50) )
                ~ too high 3.52 ~
                push("a", decimal.seven(#numbers31, -20) )
                ~ fits: 3.52 ~
                push("a", decimal.eight(#0, none(), -10) )
            ]
            """
        )
        path.collect()
        expected = [False, False, True, True, False, False, False, True]
        assert "a" in path.variables
        a = path.variables["a"]
        assert a == expected

    def test_function_decimal3(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
                ~ return-mode: matches
                  validation-mode: no-raise, no-stop
                  explain-mode:no-explain ~
                ${NUMBERS}[1*] [
                    or(
                        decimal.strict(#1),
                        decimal.strict.notnone(#2)
                    )
                ]"""
        )
        lines = path.collect()
        assert len(lines) == 2

    def test_function_decimal4(self):
        path = CsvPath()
        path.parse(
            f"""
                ~ return-mode: matches
                  validation-mode: no-raise, no-stop ~
                ${NUMBERS}[1*] [
                        decimal.weak(#1)
                        decimal.weak.notnone(#2)
                ]"""
        )
        lines = path.collect()
        assert len(lines) == 7

    def test_function_decimal5(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
                ~ return-mode: matches
                  validation-mode: no-raise, no-stop, collect
                  explain-mode:no-explain ~
                ${NUMBERS5}[1*] [
                        decimal.strict(#0)
                        decimal.strict(#1)
                        decimal.strict(#2)
                ]"""
        )
        lines = path.collect()
        assert len(lines) == 0
        assert len(path.errors) == 2
        # assert path.is_valid is False
