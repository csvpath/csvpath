import unittest
from csvpath.csvpath import CsvPath

PATH = "tests/test_resources/test.csv"
EMPTY = "tests/test_resources/empty.csv"


class TestFunctionsFirstLine(unittest.TestCase):
    def test_function_firstline_function1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[0-7]
            [
                regex(#say, /sniffle/)
                firstline.nocontrib() -> @line = count_lines()
                firstmatch.nocontrib() -> @match = count_lines()
                firstscan.nocontrib() -> @scan = count_lines()

            ]"""
        )
        lines = path.collect()
        print(f"\ntest_function_any_function: lines: {lines}")
        print(f"test_function_any_function: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["line"] == 0
        assert path.variables["scan"] == 0
        assert path.variables["match"] == 4

    def test_function_firstline_function2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[3-7]
            [
                regex(#say, /sniffle/)
                firstline.nocontrib() -> @line = count_lines()
                firstmatch.nocontrib() -> @match = count_lines()
                firstscan.nocontrib() -> @scan = count_lines()

            ]"""
        )
        lines = path.collect()
        print(f"\ntest_function_any_function: lines: {lines}")
        print(f"test_function_any_function: path vars: {path.variables}")
        assert len(lines) == 1
        assert "line" not in path.variables
        assert path.variables["scan"] == 3
        assert path.variables["match"] == 4

    def test_function_firstline_function3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                firstscan.nocontrib() -> print("we scan the whole file from the 0th line")
                last.nocontrib() -> print("the file has $.count_lines rows")
            ]"""
        )
        lines = path.collect()
        print(f"\ntest_function_any_function: lines: {lines}")
        print(f"test_function_any_function: path vars: {path.variables}")
        assert len(lines) == 9
        """
        assert "line" not in path.variables
        assert path.variables["scan"] == 3
        assert path.variables["match"] == 4
        """
