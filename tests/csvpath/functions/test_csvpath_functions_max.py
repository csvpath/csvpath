import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsMax(unittest.TestCase):
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
        #
        # note to self: max is done more simply today with a: @varname.increase = x
        # max() needs a rethink
        #
        path = CsvPath().parse(
            f"""${PATH}[*] [
                @the_max = max(#lastname)
                no()
            ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise, print")
        with pytest.raises(MatchException):
            path.fast_forward()
            print(f"path.vars: {path.variables}")

    def test_function_max2(self):
        path = CsvPath().parse(
            f"""${PATH}[*] [
                @the_max = max(#1)
                no()
            ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise, print")
        with pytest.raises(MatchException):
            path.fast_forward()
