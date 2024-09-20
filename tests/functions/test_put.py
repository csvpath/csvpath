import unittest
import pytest
from csvpath.matching.util.exceptions import ChildrenException
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsPut(unittest.TestCase):
    def test_function_put1(self):
        path = CsvPath()
        Save._save(path, "test_function_put1")
        print("")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                put("a", #firstname, line_number() )
            ]"""
        )
        path.fast_forward()
        print(f"\n test_function_put1: vars: {path.variables}")
        assert "a" in path.variables
        assert "Ants" in path.variables["a"]
        assert path.variables["a"]["Ants"] == 6

    def test_function_put2(self):
        path = CsvPath()
        Save._save(path, "test_function_put2")
        print("")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                put("a", #firstname )
            ]"""
        )
        path.fast_forward()
        print(f"\n test_function_put2: vars: {path.variables}")
        assert "a" in path.variables
        assert path.variables["a"] == "Frog"

    def test_function_put3(self):
        path = CsvPath()
        Save._save(path, "test_function_put3")
        print("")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                put(#firstname, line_number() )
            ]"""
        )
        path.fast_forward()
        print(f"\n test_function_put3: vars: {path.variables}")
        assert "Frog" in path.variables
        assert path.variables["Frog"] == 8

    def test_function_put4(self):
        path = CsvPath()
        Save._save(path, "test_function_put4")
        print("")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                put(#firstname, #lastname, line_number() )
            ]"""
        )
        path.fast_forward()
        print(f"\n test_function_put4: vars: {path.variables}")
        assert "Frog" in path.variables
        assert "Bat" in path.variables["Frog"]
        assert path.variables["Frog"]["Bat"] == 8
