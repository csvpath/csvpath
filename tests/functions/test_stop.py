import unittest
from csvpath.csvpath import CsvPath

PATH = "tests/test_resources/test.csv"


class TestFunctionstop(unittest.TestCase):
    def test_function_stop(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @i = concat( #firstname, #lastname)
                @c = count_lines()
                stop(@i == "FishBat")
                yes()
            ]"""
        )
        lines = path.collect()
        print(f"test_function_stop: path vars: {path.variables}")
        print(f"test_function_stop: lines: {lines}")
        assert path.stopped is True
        assert path.variables["i"] == "FishBat"
        assert path.variables["c"] == 2
        assert len(lines) == 3
