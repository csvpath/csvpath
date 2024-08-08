import unittest
from csvpath.csvpath import CsvPath

PATH = "tests/test_resources/test.csv"
EMPTY = "tests/test_resources/empty.csv"


class TestFunctionsNot(unittest.TestCase):
    def test_function_not(self):
        path = CsvPath()
        path.parse(f"${PATH}[*][not(length(#lastname)==3)]")
        lines = path.collect()
        print(f"test_function_not: lines: {len(lines)}")
        assert len(lines) == 2

    def test_function_any_function4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${EMPTY}[1-2]
            [
                @found = any(header())
                @notfound = not(any(header()))
            ]"""
        )
        lines = path.collect()
        print(f"\ntest_function_any_function: lines: {lines}")
        print(f"test_function_any_function: path vars: {path.variables}")
        assert len(lines) == 2
        assert path.variables["found"] is False
        assert path.variables["notfound"] is True

    def test_function_any_function5(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1-2]
            [
                @found = any.onmatch(header())
                @found2 = any(header())
                @notfound = not(any.onmatch(header()))
                no()
            ]"""
        )
        lines = path.collect()
        print(f"\ntest_function_any_function: lines: {lines}")
        print(f"test_function_any_function: path vars: {path.variables}")
        # assert len(lines) == 2
        assert path.variables["found"] is False
        assert path.variables["found2"] is True
        assert path.variables["notfound"] is True
