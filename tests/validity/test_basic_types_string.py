import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.util.config import Config
from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.util.exceptions import ChildrenException

PATH = "tests/test_resources/test.csv"
NUMBERS = "tests/test_resources/numbers3.csv"
PEOPLE2 = "tests/test_resources/people2.csv"


class TestValidBasicTypesString(unittest.TestCase):
    def test_validity_string1(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*][
                string("I am a string")
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_string2(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[1*][
                string("lastname", 25, 0)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 8

    def test_validity_string3(self):
        path = CsvPath()

        path.parse(
            f""" ${PATH}[*][
                string("lastname", 0, 25)
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_string4(self):
        path = CsvPath()

        path.parse(
            f""" ${PATH}[*][
                string("lastname", 2)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_validity_string5(self):
        path = CsvPath()

        path.parse(
            f""" ${PATH}[1*][
                string("I am a string", 25)
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_string6(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[1*][
                string("lastname", 100, 4)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1

    def test_validity_string7(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*][
                string(none(), 10, 0)
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_string8(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ explain-mode:explain~
            ${PEOPLE2}[3][
                string.notnone("country", 10, 0)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0
        path = CsvPath()
        path.parse(
            f"""
            ~ explain-mode:explain~
            ${PEOPLE2}[1*][
                string.notnone("country", 10, 0)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 4
