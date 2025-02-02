import unittest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"


class TestFunctionsSubtract(unittest.TestCase):
    def test_function_subtract(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = subtract( count(), length("this") ) ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["l"] == -3

    def test_function_subtract2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = subtract( 10, count(), length("this") ) ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["l"] == 5

    def test_function_subtract3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = subtract( 10, count(), length("this"), add( 2, 3) ) ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["l"] == 0
