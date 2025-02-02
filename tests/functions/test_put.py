import unittest
import pytest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"


class TestFunctionsPut(unittest.TestCase):
    def test_function_put1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1*]
            [
                put("a", #firstname, line_number() )
            ]"""
        )
        path.fast_forward()
        assert "a" in path.variables
        assert "Ants" in path.variables["a"]
        assert path.variables["a"]["Ants"] == 6

    def test_function_put2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1*]
            [
                put("a", #firstname )
            ]"""
        )
        path.fast_forward()
        assert "a" in path.variables
        assert path.variables["a"] == "Frog"

    def test_function_put3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1*]
            [
                put(#firstname, line_number() )
            ]"""
        )
        path.fast_forward()
        assert "Frog" in path.variables
        assert path.variables["Frog"] == 8

    def test_function_put4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1*]
            [
                put(#firstname, #lastname, line_number() )
            ]"""
        )
        path.fast_forward()
        assert "Frog" in path.variables
        assert "Bat" in path.variables["Frog"]
        assert path.variables["Frog"]["Bat"] == 8
