import unittest
import os
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import ChildrenException, MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
EMPTY = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}empty.csv"


class TestCsvPathFunctionsDatePart(unittest.TestCase):
    def test_function_datepart_1(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[1][
                today() == day(now())
                thisyear() == year(now())
                thismonth() == month(now())
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1

    def test_function_datepart_2(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[1][
                today() == day()
            ]"""
        )
        with pytest.raises(ChildrenException):
            path.fast_forward()

    def test_function_datepart_3(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[1][
                @d = day(#0)
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_datepart_4(self):
        path = CsvPath()
        path.parse(
            f"""${EMPTY}[1][
                @d == day(#0)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1

    def test_function_formatdate_1(self):
        path = CsvPath()
        path.parse(
            f"""${EMPTY}[1][
                thisyear() == format_date(now(), "%Y")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1

    def test_function_formatdate_2(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[1][
                @d = format_date(now())
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_formatdate_3(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[1][
                @d = format_date(now(), "fish")
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()
