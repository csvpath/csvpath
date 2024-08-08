import unittest
from csvpath.csvpath import CsvPath

PATH = "tests/test_resources/test.csv"


class TestFunctionsMin(unittest.TestCase):
    def test_function_min(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @the_min = min(#firstname)
                no()
            ]"""
        )
        lines = path.collect()
        print(f"test_function_count_in: path vars: {path.variables}")
        assert path.variables["the_min"] == "ants"
        assert len(lines) == 0

        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[3-5]
            [
                @the_min = min(#firstname, "scan")
                no()
            ]"""
        )
        lines = path.collect()
        print(f"test_function_count_in: path vars: {path.variables}")
        assert path.variables["the_min"] == "bird"
        assert len(lines) == 0

        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[3-5]
            [
                @the_min = min(#firstname, "match")
                no()
            ]"""
        )
        lines = path.collect()
        print(f"test_function_min: path vars: {path.variables}")
        assert path.variables["the_min"] is None
        assert len(lines) == 0
