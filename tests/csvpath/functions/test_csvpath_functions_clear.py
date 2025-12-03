import unittest
import os
from csvpath.csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsClear(unittest.TestCase):
    def test_function_clear_1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1-2]
            [
                @a = count_lines()
                print("$.csvpath.line_number: $.variables.a ")
                @b = @a
                clear(@a)
            ]"""
        )
        path.fast_forward()
        assert "a" not in path.variables
        assert "b" in path.variables
        assert path.variables["b"] == 3

    def test_function_clear_2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1-2]
            [
                @a = count_lines()
                print("$.csvpath.line_number: $.variables.a ")
                @b = @a
                clear("a")
            ]"""
        )
        path.fast_forward()
        assert "a" not in path.variables
        assert "b" in path.variables
        assert path.variables["b"] == 3

    def test_function_clear_3(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise~
            ${PATH}[1-2]
            [
                @a = count_lines()
                print("$.csvpath.line_number: $.variables.a ")
                @b = @a
                @c = "a"
                clear(@c)
            ]"""
        )
        path.fast_forward()
        assert "a" in path.variables
        assert "b" in path.variables
        assert "c" not in path.variables
        assert path.variables["b"] == path.variables["a"] == 3
