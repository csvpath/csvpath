import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = "tests/test_resources/test.csv"


class TestFunctionsMin(unittest.TestCase):
    def test_function_min0(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @the_min = min(line_number())
             ]"""
        ).fast_forward()
        assert path.variables["the_min"] == 0

    def test_function_min1(self):
        path = CsvPath()

        path.parse(
            f"""
            ${PATH}[*]
            [
                @the_min = min(#firstname)
                no()
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_min2(self):
        path = CsvPath()

        path.parse(
            f"""
            ${PATH}[3-5]
            [
                @the_min = min(#firstname, "scan")
                no()
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_min3(self):
        path = CsvPath()

        path.parse(
            f"""
            ${PATH}[3-5]
            [
                @the_min = min(#firstname, "match")
                no()
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()
