import unittest
import os
from csvpath.csvpath import CsvPath

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"


class TestFunctionsDivide(unittest.TestCase):
    def test_function_divide(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[2]
            [ @l = divide( 100, 10 ) ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["l"] == 10

    def test_function_divide2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[2-3]
            [ @l = divide( 100, count() ) ]"""
        )
        lines = path.collect()
        assert len(lines) == 2
        assert path.variables["l"] == 50

    def test_function_divide3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[2-3]
            [ @l = divide( 100, count(), add(2,3) ) ]"""
        )
        lines = path.collect()
        assert len(lines) == 2
        assert path.variables["l"] == 10

    def test_function_divide4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[2-3]
            [ @l = divide( 100, 0 ) ]"""
        )
        lines = path.collect()
        assert len(lines) == 2
        import math

        assert math.isnan(path.variables["l"])
