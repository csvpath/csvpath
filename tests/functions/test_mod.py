import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsMod(unittest.TestCase):
    def test_function_mod1(self):
        path = CsvPath()
        Save._save(path, "test_function_mod1")
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

    def test_function_mod2(self):
        path = CsvPath()
        Save._save(path, "test_function_mod2")
        path.parse(
            f""" ${PATH}[*] [
                @mod = mod(count_lines(), 2)
                @int = int(@mod)
            ]
            """
        )
        print("")
        lines = path.collect()
        print(f"test_function_mod2: path vars: {path.variables}")
        print(f"test_function_mod2: lines: {lines}")
        assert path.variables["mod"] == 0.0
        assert path.variables["int"] == 0

    def test_function_equal_mod(self):
        path = CsvPath()
        Save._save(path, "test_function_equal_mod")
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
        print(f"test_function_equal_mod: path vars: {path.variables}")
        print(f"test_function_equal_mod: lines: {lines}")
        assert path.variables["c"] == 5
        assert len(lines) == 9

    def test_function_int1(self):
        path = CsvPath()
        Save._save(path, "test_function_int1")
        path.parse(
            f""" ${PATH}[*] [
                @st = int(" ")
                @no = int(none())
                @bo = int(no())
            ]
            """
        )
        print("")
        lines = path.collect()
        print(f"test_function_int1: path vars: {path.variables}")
        print(f"test_function_int1: lines: {lines}")
        assert path.variables["st"] == 0
        assert path.variables["no"] == 0
        assert path.variables["bo"] == 0
