import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsSlice(unittest.TestCase):
    def test_function_slice_1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [
                push("a", 1)
                push("a", 23)
                push("a", 3)
                push("a", -2)
                @b = slice("a", 1, 2)
            ]"""
        )
        path.fast_forward()
        assert "b" in path.variables
        assert path.variables["b"] == [23, 3]

    def test_function_slice_2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [
                push("a", 1)
                push("a", 23)
                push("a", 3)
                push("a", -2)
                @b = slice("a", 0, 2)
            ]"""
        )
        path.fast_forward()
        assert "b" in path.variables
        assert path.variables["b"] == [1, 23, 3]

    def test_function_slice_3(self):
        path = CsvPath()
        path.parse(
            f""" ~ validation-mode:raise, collect~
            ${PATH}[1]
            [
                push("a", 1)
                push("a", 23)
                push("a", 3)
                push("a", -2)
                @b = slice("a", 2, 0)
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_slice_4(self):
        path = CsvPath()
        path.parse(
            f""" ~ validation-mode:raise, collect~
            ${PATH}[1]
            [
                push("a", 1)
                push("a", 23)
                push("a", 3)
                push("a", -2)
                @b = slice("a", -1, 0)
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_slice_5(self):
        path = CsvPath()
        path.parse(
            f""" ~ validation-mode:raise, collect~
            ${PATH}[1]
            [
                push("a", 1)
                push("a", 23)
                push("a", 3)
                push("a", -2)
                @b = slice("a", 1, 20)
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_slice_6(self):
        path = CsvPath()
        path.parse(
            f""" ~ validation-mode:raise, collect~
            ${PATH}[1]
            [
                push("a", 1)
                push("a", 23)
                push("a", 3)
                push("a", -2)
                @b = slice("c", 1, 3)
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()
