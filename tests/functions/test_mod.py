import unittest
from csvpath.csvpath import CsvPath

PATH = "tests/test_resources/test.csv"


class TestFunctionsMod(unittest.TestCase):
    def test_function_mod1(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*] [ ~this is a comment~
                @mod = mod(count_lines(), 2)
                ~another comment~
                @mod == 0.0
                print.onmatch("$.variables.mod")
            ]
            """
        )
        print("")
        lines = path.collect()
        print(f"test_function_mod1: path vars: {path.variables}")
        print(f"test_function_mod1: lines: {lines}")
        assert path.variables["mod"] == 0.0
        assert len(lines) == 5

    def test_function_equals_mod(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*] [
                @m = mod(count_lines(), 2)
                @c = count( equals( @m, 0) )
                print.onmatch("printing: $.variables, count: $.match_count")
                ~ comment ~
            ]
            """
        )
        print("")
        lines = path.collect()
        print(f"test_function_equals_mod: path vars: {path.variables}")
        print(f"test_function_equals_mod: lines: {lines}")
        assert path.variables["c"] == 5
        assert len(lines) == 9
