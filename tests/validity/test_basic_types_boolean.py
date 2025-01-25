import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.util.config import Config
from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.util.exceptions import ChildrenException

PATH = "tests/test_resources/test.csv"
NUMBERS = "tests/test_resources/numbers3.csv"


class TestValidBasicTypesBoolean(unittest.TestCase):
    def test_validity_boolean1(self):
        path = CsvPath()

        path.parse(
            f""" ${PATH}[*][
                boolean(yes())
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_boolean2(self):
        path = CsvPath()

        path.parse(
            f""" ~ None is acceptable if not notnone but it is not
                   a boolean value so we get nothing here ~
            ${PATH}[*][
                boolean(none())
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_validity_boolean3(self):
        path = CsvPath()

        path.parse(
            f""" ~ 1 is the 2nd column. it doesn't have booleans.
                   validation-mode: no-raise, no-stop
                 ~
            ${PATH}[*][
                boolean("1")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_validity_boolean4(self):
        path = CsvPath().parse(
            f""" ~ -1 is not a boolean and is not convertable to a boolean ~
            ${PATH}[*][ boolean(-1)]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_boolean45(self):
        path = CsvPath().parse(f"""${PATH}[*][boolean(5)]""")
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_boolean5(self):
        path = CsvPath().parse(f"""${PATH}[*][ boolean("fish") ]""")
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_boolean6(self):
        path = CsvPath().parse(
            f""" ~ note that @b standing alone is an existance test.
                   that means it's not yes()'s boolean or the boolean()'s
                   validation that yes() is a boolean. it is the
                   existance of a value @b. ~
            ${PATH}[*][
                @b = boolean(yes())
                @b
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_boolean7(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*][
                ~ yes, it's a bool ~
                @b = boolean(no())
                ~ yes, it exists ~
                @b
                ~ no, it is not True ~
                @b.asbool
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_validity_boolean8(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*][
                @b.asbool = boolean(false())
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0
