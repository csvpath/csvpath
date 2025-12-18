import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.util.config import Config
from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.util.exceptions import ChildrenException

NUMBERS = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}numbers3.csv"
NUMBERS4 = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}numbers4.csv"


class TestCsvPathValidityValidBasicTypesInteger(unittest.TestCase):
    def test_function_integer1(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(
            f"""
                ~ return-mode: matches
                  validation-mode: no-raise, no-stop, print ~
                ${NUMBERS}[6] [
                        integer(#1)
                ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_function_integer2a(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        #
        # 1.0 is not an integer.strict because of the .0
        #
        path.parse(
            f"""
                ~ return-mode: matches
                  validation-mode: no-raise, no-stop, print ~
                ${NUMBERS4}[9] [
                        integer.strict(#numbers32)
                ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_function_integer2b(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        #
        # 1.0 is an integer without strict because the .0 doesn't disqualify it
        #
        path.parse(
            f"""
                ~ return-mode: matches
                  validation-mode: no-raise, no-stop, print ~
                ${NUMBERS4}[9] [
                        integer(#numbers32)
                ]"""
        )
        lines = path.collect()
        assert len(lines) == 1

    def test_function_integer3a(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        #
        # 100 is not between 50 and 1
        #
        path.parse(
            f"""
                ~ return-mode: matches
                  validation-mode: no-raise, no-stop, print ~
                ${NUMBERS4}[8] [
                        integer(#numbers32, 50, 1)
                ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_function_integer3b(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        #
        # 100 is between 150 and 99
        #
        path.parse(
            f"""
                ~ return-mode: matches
                  validation-mode: no-raise, no-stop, print ~
                ${NUMBERS4}[8] [
                        integer(#numbers32, 150, 99)
                ]"""
        )
        lines = path.collect()
        assert len(lines) == 1

    def test_function_integer3c(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        #
        # -20 is between -15 and -50
        #
        path.parse(
            f"""
                ~ return-mode: matches
                  validation-mode: no-raise, no-stop, print ~
                ${NUMBERS4}[7] [
                        integer(#numbers32, -15, -50)
                ]"""
        )
        lines = path.collect()
        assert len(lines) == 1

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

    def test_function_integer6(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        #
        # none is not allowed
        #
        path.parse(
            f"""
                ~ return-mode: matches
                  validation-mode: no-raise, no-stop, print ~
                ${NUMBERS4}[3] [
                        integer.notnone(#numbers33)
                ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_function_integer7(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        #
        # none is allowed
        #
        path.parse(
            f"""
                ~ return-mode: matches
                  validation-mode: no-raise, no-stop, print ~
                ${NUMBERS4}[3] [
                        integer(#numbers33)
                ]"""
        )
        lines = path.collect()
        assert len(lines) == 1

    def test_function_integer_8(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
                ~ return-mode: matches
                  validation-mode: raise, no-stop, collect, print
                  explain-mode:no-explain ~
                ${NUMBERS}[1*] [
                        integer.distinct(#1)
                ]"""
        )
        with pytest.raises(MatchException):
            path.collect()
