import unittest
from csvpath import CsvPath

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
        lines = path.collect()
        assert path.variables["mod"] == 1.0
        assert len(lines) == 4

    def test_function_mod2(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*] [
                @mod = mod(count_lines(), 2)
                @int = int(@mod)
            ]
            """
        )
        path.collect()
        assert path.variables["mod"] == 1.0
        assert path.variables["int"] == 1

    def test_function_mod3(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*] [
                @m = mod(count_lines(), 2)
                @c = count( equals( @m, 0) )
                print.onmatch("printing: count: $.csvpath.match_count")
                ~ comment ~
            ]
            """
        )
        lines = path.collect()
        assert path.variables["c"] == 5
        assert len(lines) == 9
