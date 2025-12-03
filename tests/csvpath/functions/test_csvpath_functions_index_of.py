import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsIndexOf(unittest.TestCase):
    def test_function_index_of_1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [
                push("a", "super")
                push("a", "duper")
                push("a", "frog")
                @pos = index_of(@a, "duper")
                print("$.csvpath.line_number: $.variables.pos")
            ]"""
        )
        path.fast_forward()
        assert "a" in path.variables
        assert "pos" in path.variables
        assert path.variables["pos"] == 1

    def test_function_index_of_2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [
                push("a", "super")
                push("a", "duper")
                push("a", "frog")
                @pos = index_of("a", "duper")
                print("$.csvpath.line_number: $.variables.pos")
            ]"""
        )
        path.fast_forward()
        assert "a" in path.variables
        assert "pos" in path.variables
        assert path.variables["pos"] == 1

    def test_function_index_of_3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [
                put("a")
                push("a", "super")
                @pos = index_of("a", "super")
                print("$.csvpath.line_number: $.variables.pos")
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()
