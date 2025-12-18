import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.util.config import Config
from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.util.exceptions import ChildrenException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
NUMBERS = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}numbers3.csv"
TYPES = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}types2.csv"

TYPES3 = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}types3.csv"


class TestCsvPathValidityValidBasicTypesBoolean(unittest.TestCase):
    def test_validity_boolean1(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f""" ${PATH}[*][
                boolean(yes())
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_boolean2(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
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
        path.config.add_to_config("errors", "csvpath", "raise")
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

    def test_validity_boolean5(self):
        path = CsvPath().parse(f"""${PATH}[*][boolean(5)]""")
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_boolean6(self):
        path = CsvPath().parse(f"""${PATH}[*][ boolean("fish") ]""")
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_boolean7(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(
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

    def test_validity_boolean8(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
            ~ validation-mode:no-raise~
            ${PATH}[1][
                ~ yes, it's a bool ~
                @b = boolean("say")
                ~ yes, it exists ~
                @b
                ~ no, it is not True ~
                @b.asbool
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_validity_boolean9(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f""" ${PATH}[1][
                ~ yes, it's a bool ~
                @b = boolean(no())
                ~ yes, it exists ~
                @b
                ~ we can make it not True ~
                not( @b.asbool )
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_validity_boolean_10(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f""" ${PATH}[1][
                @b.asbool = boolean( false() )
                not( @b.asbool )
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_validity_boolean_11(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f""" ${TYPES}[*][
                boolean.distinct.morning(#2)
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_boolean_12(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f""" ${TYPES3}[1*][
                ~ checks that false == False for purposes of distinct,
                  and that only about 4 lines possible when distinct: true, false, empty, skipped header. ~
                print("$.csvpath.line_number: $.headers.2")
                boolean.distinct.morning(#2)
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()
