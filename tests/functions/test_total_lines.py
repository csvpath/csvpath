import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestTotalLines(unittest.TestCase):
    def test_function_total_lines(self):
        path = CsvPath()
        Save._save(path, "test_function_total_lines")
        path.parse(
            f"""
            ${PATH}[1]
            [ @total = total_lines() ]"""
        )
        lines = path.collect()
        print(f"test_function_total_lines: lines: {lines}")
        print(f"test_function_total_lines: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["total"] == 9
