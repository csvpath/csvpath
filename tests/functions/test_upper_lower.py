import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsUpperLower(unittest.TestCase):
    def test_function_upper_and_lower1(self):
        path = CsvPath()
        Save._save(path, "test_function_upper_and_lower")
        path.parse(
            f"""${PATH}[*][ @upper = upper(#firstname)
            @lower = lower(#firstname) ]"""
        )
        lines = path.collect()
        print(f"test_function_upper_and_lower: lines: {len(lines)}")
        print(f"test_function_upper_and_lower: path vars: {path.variables}")
        assert "upper" in path.variables
        assert "lower" in path.variables
        assert path.variables["lower"] == "frog"
        assert path.variables["upper"] == "FROG"

    def test_function_upper_and_lower2(self):
        path = CsvPath()
        Save._save(path, "test_function_upper_and_lower")
        path.parse(
            f"""${PATH}[*][
             upper(#firstname)
             lower(#firstname) ]"""
        )
        lines = path.collect()
        print(f"test_function_upper_and_lower: lines: {len(lines)}")
        print(f"test_function_upper_and_lower: path vars: {path.variables}")
        assert len(lines) == 9
