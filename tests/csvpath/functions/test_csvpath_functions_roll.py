import unittest
import os
import pytest
import datetime
from datetime import date, timezone
from csvpath import CsvPath
from csvpath.matching.util.exceptions import ChildrenException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
NUMBERS = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}numbers.csv"


class TestCsvPathFunctionsRoll(unittest.TestCase):
    def test_function_roll_1(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[2][
                @d = date("2025-11-21")
                @r = roll(@d, 2, "day")
        ]"""
        )
        path.fast_forward()
        assert "r" in path.variables
        assert path.variables["r"] == date(2025, 11, 23)

    def test_function_roll_2(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[2][
                @r = roll( none(), 2, "day")
        ]"""
        )
        path.fast_forward()
        assert "r" in path.variables
        assert path.variables["r"] is None

    def test_function_roll_3(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[2][
                @r = roll( none(), 2, "fish")
        ]"""
        )
        with pytest.raises(ChildrenException):
            path.fast_forward()

    def test_function_roll_4(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[2][
                @r = roll( none(), "day", 1)
        ]"""
        )
        with pytest.raises(ChildrenException):
            path.fast_forward()

    def test_function_roll_5(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[2][
                @d = date("2025-11-21")
                @r = roll(@d, 1, "month")
        ]"""
        )
        path.fast_forward()
        assert "r" in path.variables
        assert path.variables["r"] == date(2025, 12, 21)

    def test_function_roll_6(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[2][
                @d = date("2025-11-21")
                @r = roll(@d, 1, "year")
        ]"""
        )
        path.fast_forward()
        assert "r" in path.variables
        assert path.variables["r"] == date(2026, 11, 21)

    def test_function_roll_7(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[2][
                @d = datetime("2025-11-21 10:30:00")
                @r = roll(@d, 1, "hour")
        ]"""
        )
        path.fast_forward()
        assert "r" in path.variables
        r = path.variables["r"]
        c = datetime.datetime(2025, 11, 21, 11, 30, 0)
        c = c.replace(tzinfo=timezone.utc)
        assert r == c

    def test_function_roll_8(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[2][
                @d = datetime("2025-11-21 10:30:00")
                @r = roll(@d, 1, "minute")
        ]"""
        )
        path.fast_forward()
        assert "r" in path.variables
        r = path.variables["r"]
        c = datetime.datetime(2025, 11, 21, 10, 31, 0)
        c = c.replace(tzinfo=timezone.utc)
        assert r == c

    def test_function_roll_9(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[2][
                @d = datetime("2025-11-21 10:30:00")
                @r = roll(@d, 3, "second")
        ]"""
        )
        path.fast_forward()
        assert "r" in path.variables
        r = path.variables["r"]
        c = datetime.datetime(2025, 11, 21, 10, 30, 3)
        c = c.replace(tzinfo=timezone.utc)
        assert r == c

    def test_function_roll_10(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[2][
                @d = date("2025-11-21")
                @r = roll(@d, -1, "month")
        ]"""
        )
        path.fast_forward()
        assert "r" in path.variables
        assert path.variables["r"] == date(2025, 10, 21)

    def test_function_roll_11(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[2][
                @d = date("2025-11-21")
                @r = roll(@d, -3, "years")
        ]"""
        )
        path.fast_forward()
        assert "r" in path.variables
        assert path.variables["r"] == date(2022, 11, 21)
