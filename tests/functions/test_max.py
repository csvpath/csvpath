import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = "tests/test_resources/test.csv"


class TestFunctionsMax(unittest.TestCase):
    def test_function_max0(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*]
            [
                @the_max = max(line_number())
             ]"""
        ).fast_forward()
        assert path.variables["the_max"] == 8

    def test_function_max1(self):
        path = CsvPath().parse(
            f"""${PATH}[*] [
                @the_max = max(#firstname)
                no()
            ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_max2(self):
        path = CsvPath().parse(
            f"""${PATH}[*] [
                @the_max = max(#1)
                no()
            ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.fast_forward()
