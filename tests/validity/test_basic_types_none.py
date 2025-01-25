import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.util.config import Config
from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.util.exceptions import ChildrenException

PATH = "tests/test_resources/test.csv"
NUMBERS = "tests/test_resources/numbers3.csv"


class TestValidBasicTypesNone(unittest.TestCase):
    def test_validity_none0(self):
        path = CsvPath().parse(
            f"""~id:validity_none0~ ${PATH}[*][
                line(
                    none(),
                    wildcard()
                )
            ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise, print, collect, stop")
        path.modes.update()
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_none01(self):
        path = CsvPath().parse(
            f"""~id:validity_none01~ ${PATH}[*][
                line(
                    integer(#firstname),
                    boolean( yes() ),
                    wildcard()
                )
            ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise, print, collect, stop")
        path.modes.update()
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_none1(self):
        path = CsvPath().parse(
            f"""~id:validity_none1~ ${PATH}[*][ none("2024-01-01") ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise, print, collect, stop")
        path.modes.update()
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_none2(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise, print, collect, stop")
        path.parse(
            f"""~id:validity_none2~ ${PATH}[*][
                none(none())
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_none3(self):
        path = CsvPath().parse(f"""~id:none3~ ${PATH}[*][ none(-1) ]""")
        path.config.add_to_config("errors", "csvpath", "raise, print, collect, stop")
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_none4(self):
        path = CsvPath().parse(f"""~id:validity_none4~ ${PATH}[*][ none(5, 9)]""")
        path.config.add_to_config("errors", "csvpath", "raise, print, collect, stop")
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_none5(self):
        path = CsvPath().parse(
            """
                ~
                    id:validity_none5
                    validation-mode:no-raise, no-stop
                ~
                $tests/test_resources/food.csv[10][
                none(#3)
            ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise, print, collect, stop")
        lines = path.collect()
        assert len(lines) == 1

    def test_validity_none6(self):
        path = CsvPath().parse(
            """ ~
                    id:validity_none5
                    validation-mode:no-raise, no-stop
                ~
                $tests/test_resources/food.csv[9-10][
                none(#year)
            ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise, print, collect, stop")
        lines = path.collect()
        assert len(lines) == 1
