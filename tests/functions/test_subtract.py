import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

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

    def test_function_subtract4(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = subtract(1) @l2 = minus(1) ]"""
        )
        path.fast_forward()
        print(f"test_function_subtract4: {path.variables}")
        assert path.variables["l"] == -1
        assert path.variables["l2"] == -1

    def test_function_subtract5(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = subtract("five") ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_subtract6(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(
            f"""
            ${PATH}[1]
            [
             @d = 1.5
             @l = minus(@d)
            ]"""
        )
        path.fast_forward()
        print(f"test_function_subtract4: {path.variables}")
        assert path.variables["l"] == -1.5
