import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsMin(unittest.TestCase):
    def test_function_min1(self):
        path = CsvPath()
        Save._save(path, "test_function_min1")
        path.parse(
            f"""
            ${PATH}[*]
            [
                @the_min = min(#firstname)
                no()
            ]"""
        )
        lines = path.collect()
        print(f"test_function_min1: path vars: {path.variables}")
        assert path.variables["the_min"] == "ants"
        assert len(lines) == 0

    def test_function_min2(self):
        path = CsvPath()
        Save._save(path, "test_function_min2")
        path.parse(
            f"""
            ${PATH}[3-5]
            [
                @the_min = min(#firstname, "scan")
                no()
            ]"""
        )
        lines = path.collect()
        print(f"test_function_min2: path vars: {path.variables}")
        assert path.variables["the_min"] == "bird"
        assert len(lines) == 0

    def test_function_min3(self):
        path = CsvPath()
        Save._save(path, "test_function_min3")
        path.parse(
            f"""
            ${PATH}[3-5]
            [
                @the_min = min(#firstname, "match")
                no()
            ]"""
        )
        lines = path.collect()
        print(f"test_function_min3: path vars: {path.variables}")
        assert path.variables["the_min"] is None
        assert len(lines) == 0
