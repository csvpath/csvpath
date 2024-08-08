import unittest
from csvpath.csvpath import CsvPath

PATH = "tests/test_resources/test.csv"


class TestFunctionsUpperLower(unittest.TestCase):
    def test_function_upper_and_lower(self):
        path = CsvPath()
        path.parse(
            f"${PATH}[*][ @upper = upper(#firstname) @lower = lower(#firstname) ]"
        )
        lines = path.collect()
        print(f"test_function_count_in: lines: {len(lines)}")
        print(f"test_function_count_in: path vars: {path.variables}")
        assert "upper" in path.variables
        assert "lower" in path.variables
        assert path.variables["lower"] == "frog"
        assert path.variables["upper"] == "FROG"
