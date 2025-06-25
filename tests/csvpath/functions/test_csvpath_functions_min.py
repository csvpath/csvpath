import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsMin(unittest.TestCase):
    def test_function_min0(self):
        path = (
            CsvPath()
            .parse(
                f""" ${PATH}[*][
                @the_min = min(line_number())
             ]"""
            )
            .fast_forward()
        )
        assert path.variables["the_min"] == 0

    def test_function_min05(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*][
                @the_min = min(line_number(), "foo")
             ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_min1(self):
        path = CsvPath().parse(
            f""" ${PATH}[*][
                @the_min = min(#firstname)
                no()
            ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_min2(self):
        path = CsvPath().parse(
            f"""${PATH}[3-5][
                @the_min = min(#firstname)
                no()
            ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_min3(self):
        path = CsvPath().parse(
            f"""${PATH}[3-5][
                @the_min = min(#firstname)
                no()
            ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.fast_forward()
