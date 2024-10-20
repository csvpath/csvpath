import unittest
import pytest
from csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/numbers.csv"


class TestFunctionsSum(unittest.TestCase):
    def test_function_sum1(self):
        path = CsvPath()
        Save._save(path, "test_function_sum1")
        path.parse(
            f"""
            ${PATH}[1*]
            [ @l = sum(#0) ]"""
        )
        lines = path.collect()
        print(f"test_function_sum1: lines: {lines}")
        print(f"test_function_sum1: path vars: {path.variables}")
        assert path.variables["l"] == 6

    def test_function_sum2(self):
        print("")
        path = CsvPath()
        Save._save(path, "test_function_sum2")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                @l = sum.onmatch(#0)
                lt(count_lines(),3)
            ]"""
        )
        lines = path.collect()
        print(f"test_function_sum2: lines: {lines}")
        print(f"test_function_sum2: path vars: {path.variables}")
        # skip line 0, sum lines 1 and 2 == 3 and stop
        assert path.variables["l"] == 3

    def test_function_sum3(self):
        path = CsvPath()
        Save._save(path, "test_function_sum3")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                @notsum = add( @notsum, #0)
                sum(#0)
            ]"""
        )
        lines = path.collect()
        print(f"test_function_sum3: lines: {lines}")
        print(f"test_function_sum3: path vars: {path.variables}")
        assert path.variables["sum"] == 6
        assert path.variables["notsum"] == 6

    def test_function_sum4(self):
        path = CsvPath()
        Save._save(path, "test_function_sum3")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                sum(#0)
            ]"""
        )
        lines = path.collect()
        print(f"test_function_sum3: lines: {lines}")
        print(f"test_function_sum3: path vars: {path.variables}")
        assert len(lines) == 7
        assert path.variables["sum"] == 6
