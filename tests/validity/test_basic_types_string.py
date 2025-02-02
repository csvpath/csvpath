import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.util.config import Config
from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.util.exceptions import ChildrenException

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"
NUMBERS = f"tests{os.sep}test_resources{os.sep}numbers3.csv"
PEOPLE2 = f"tests{os.sep}test_resources{os.sep}people2.csv"


class TestValidBasicTypesString(unittest.TestCase):
    def test_validity_string1(self):
        path = CsvPath().parse(f"""${PATH}[*][string("I am a string")]""")
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_string2(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f""" ${PATH}[1*][
                string(#lastname, 25, 0)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 8

    def test_validity_string3(self):
        path = CsvPath().parse(f"""${PATH}[*][string(#lastname, 0, 25)]""")
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_string4(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f""" ${PATH}[*][
                string(#lastname, 2)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_validity_string5(self):
        path = CsvPath().parse(f"""${PATH}[1*][string("I am a string", 25)]""")
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_string6(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f""" ${PATH}[1*][
                string(#lastname, 100, 4)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1

    def test_validity_string7(self):
        path = CsvPath().parse(f"""${PATH}[*][string.notnone(none(), 10, 0)]""")
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_string8(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "print")
        path.parse(
            f"""
            ~ explain-mode:explain~
            ${PEOPLE2}[3][
                string.notnone(#country, 10, 0)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_validity_string9(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "print")
        path.parse(
            f"""
            ~ explain-mode:explain~
            ${PEOPLE2}[1*][
                string.notnone(#country, 10, 0)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 4
