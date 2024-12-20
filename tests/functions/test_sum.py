import unittest
import pytest
from csvpath import CsvPath

PATH = "tests/test_resources/numbers.csv"


class TestFunctionsSum(unittest.TestCase):
    def test_function_sum1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1*]
            [ @l = sum(#0) ]"""
        )
        path.collect()
        assert path.variables["l"] == 6

    def test_function_sum2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1*]
            [
                @l = sum.onmatch(#0)
                lt(count_lines(),3)
            ]"""
        )
        path.collect()
        assert path.variables["l"] == 3

    def test_function_sum3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1*]
            [
                @notsum = add( @notsum, #0)
                sum(#0)
            ]"""
        )
        path.collect()
        assert path.variables["sum"] == 6
        assert path.variables["notsum"] == 6

    def test_function_sum4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1*]
            [
                sum(#0)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 7
        assert path.variables["sum"] == 6
