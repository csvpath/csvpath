import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionStop(unittest.TestCase):
    def test_function_stop(self):
        path = CsvPath()
        Save._save(path, "test_function_stop")
        path.parse(
            f"""
            ${PATH}[*]
            [
                @i = concat( #firstname, #lastname)
                @c = count_lines()
                yes()
                stop(@i == "FishBat")
            ]"""
        )
        lines = path.collect()
        print(f"test_function_stop: path vars: {path.variables}")
        print(f"test_function_stop: lines: {lines}")
        assert path.stopped is True
        assert path.variables["i"] == "FishBat"
        assert path.variables["c"] == 2
        assert len(lines) == 3
