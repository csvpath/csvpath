import unittest
from csvpath.csvpath import CsvPath

PATH = "tests/test_resources/test.csv"


class TestFunctionsMax(unittest.TestCase):
    def test_function_max1(self):
        print("")
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @the_max = max(#firstname)
                no()
            ]"""
        )
        lines = path.collect()
        print(f"test_function_max: path vars: {path.variables}")
        assert path.variables["the_max"] == "slug"
        assert len(lines) == 0

    def test_function_max2(self):
        print("")
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @the_max = max(#1)
                no()
            ]"""
        )
        lines = path.collect()
        print(
            f"test_function_max2: should not ignore header row. path vars: {path.variables}"
        )
        assert path.variables["the_max"] == "lastname"
        assert len(lines) == 0
