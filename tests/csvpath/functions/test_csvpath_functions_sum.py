import unittest
import pytest
import os
from csvpath import CsvPath

NUMBERS = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}numbers.csv"


class TestCsvPathFunctionsSum(unittest.TestCase):
    def test_function_sum1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${NUMBERS}[1*]
            [ @l = sum(#0) ]"""
        )
        path.collect()
        print(f"vars: {path.variables}")
        assert path.variables["l"] == 6

    def test_function_sum2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${NUMBERS}[1*]
            [
                @l = sum.onmatch(#0)
                lt(count_lines(),3)
            ]"""
        )
        path.collect()
        #
        # count_lines() includes the header: it is 2 on line 1 and 3 on
        # line 2, so lt(count_lines(),3) matches line 1 only. this expected
        # 3 (lines 1 and 2) while lt() behaved as lte() -- issue #301.
        #
        assert path.variables["l"] == 1

    def test_function_sum3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${NUMBERS}[1*]
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
            ${NUMBERS}[1*]
            [
                sum(#0)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 7
        assert path.variables["sum"] == 6
