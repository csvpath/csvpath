import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.util.config import Config
from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.util.exceptions import ChildrenException
from tests.save import Save

PATH = "tests/test_resources/test.csv"
NUMBERS = "tests/test_resources/numbers3.csv"


class TestValidBasicTypesNone(unittest.TestCase):
    def _config(self, path) -> None:
        path.config.add_to_config("errors", "csvpath", "raise, print, collect, stop")

    def test_validity_none1(self):
        path = CsvPath()
        self._config(path)
        Save._save(path, "test_validity_none")
        path.parse(
            f"""~id:validity_none1~ ${PATH}[*][
                none("2024-01-01")
            ]"""
        )
        path.modes.update()
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_none2(self):
        path = CsvPath()
        self._config(path)
        Save._save(path, "test_validity_none2")
        path.parse(
            f"""~id:validity_none2~ ${PATH}[*][
                none(none())
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_none3(self):
        path = CsvPath()
        self._config(path)
        Save._save(path, "test_validity_none3")
        path.parse(
            f"""~id:validity_none3~ ${PATH}[*][
                none(-1)
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_none4(self):
        path = CsvPath()
        self._config(path)
        Save._save(path, "test_validity_none4")
        path.parse(
            f"""~id:validity_none4~ ${PATH}[*][
                none(5, 9)
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_none5(self):
        path = CsvPath()
        self._config(path)
        Save._save(path, "test_validity_none5")
        print("")
        path.parse(
            """
                ~
                    id:validity_none5
                    validation-mode:no-raise, no-stop
                ~
                $tests/test_resources/food.csv[10][
                none(#3)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1

    def test_validity_none6(self):
        path = CsvPath()
        self._config(path)
        Save._save(path, "test_validity_none6")
        print("")
        path.parse(
            """
                ~
                    id:validity_none5
                    validation-mode:no-raise, no-stop
                ~
                $tests/test_resources/food.csv[9-10][
                none("year")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
