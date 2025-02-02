import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.util.config import Config
from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.util.exceptions import ChildrenException

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"
NUMBERS = f"tests{os.sep}test_resources{os.sep}numbers3.csv"
DATES = f"tests{os.sep}test_resources{os.sep}dates.csv"
DATES2 = f"tests{os.sep}test_resources{os.sep}dates2.csv"


class TestValidBasicTypesDate(unittest.TestCase):
    def test_validity_date1(self):
        path = CsvPath().parse(f"""~id:date1~ ${PATH}[*][ date()]""")
        path.config.add_to_config("errors", "csvpath", "raise, print")
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_validity_date2(self):
        path = CsvPath().parse(f"""~id:date2~ ${PATH}[*][date.notnone(none())]""")
        path.config.add_to_config("errors", "csvpath", "raise, print")
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_validity_date3(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""~id:validity_date3~ ${PATH}[*][
                date("2024-01-01")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_date4(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""~id:validity_date4~ ${PATH}[*][
                @d = date("2024-01-01")
                date(@d)]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_date5(self):
        path = CsvPath().parse(
            f"""~id:validity_date5~ ${PATH}[*][
                date("the 3rd of feb")
            ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_date6(self):
        path = CsvPath().parse(
            f"""~id:validity_date6~ ${PATH}[*][
                date("the 3rd of feb", "%Y")
            ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_date7(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""~id:validity_date7~
            ${DATES}[1][
                date(#date, "%Y-%m-%d")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1

    def test_validity_date8(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""~id:validity_date7~
            ${DATES}[1][
                date(#date)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1

    def test_validity_date9(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""~
                    id:validity_date7
                    validation-mode:no-raise
                ~
            ${DATES2}[8][
                date.notnone(#date)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_validity_now1(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""~id:validity_now1~ ${PATH}[*][
                now("%Y")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_now2(self):
        path = CsvPath().parse(f"""~id:validity_now2~ ${PATH}[*][today("%Y")]""")
        path.config.add_to_config("errors", "csvpath", "raise, print")
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_now3(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(f"""~id:validity_now3~ ${PATH}[*][ now() ]""")
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_now4(self):
        path = CsvPath().parse(
            f"""~id:validity_now4~ ${PATH}[*][
                now("2024-01-01","%Y")
            ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise, print")
        with pytest.raises(MatchException):
            path.collect()
