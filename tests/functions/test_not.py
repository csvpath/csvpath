import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"
EMPTY = "tests/test_resources/empty.csv"


class TestFunctionsNot(unittest.TestCase):
    def test_function_not(self):
        path = CsvPath()
        Save._save(path, "test_function_not")
        path.parse(f"${PATH}[*][not(length(#lastname)==3)]")
        lines = path.collect()
        print(f"test_function_not: lines: {len(lines)}")
        assert len(lines) == 2

    def test_function_any_function4(self):
        path = CsvPath()
        Save._save(path, "test_function_any_function4")
        path.parse(
            f"""
            ${EMPTY}[1-2]
            [
                @found = any(headers())
                @notfound = not(any(headers()))
            ]"""
        )
        lines = path.collect()
        print(f"\test_function_any_function4: lines: {lines}")
        print(f"test_function_any_function4: path vars: {path.variables}")
        assert len(lines) == 2
        assert path.variables["found"] is False
        assert path.variables["notfound"] is True

    def test_function_any_function5(self):
        path = CsvPath()
        Save._save(path, "test_function_any_function5")
        path.parse(
            f"""
            ${PATH}[1-2]
            [
                @found = any.onmatch(headers())
                @found2 = any(headers())
                @notfound = not(any.onmatch(headers()))
                no()
            ]"""
        )
        lines = path.collect()
        print(f"\test_function_any_function5: lines: {lines}")
        print(f"test_function_any_function5: path vars: {path.variables}")
        # assert len(lines) == 2
        assert path.variables["found"] is False
        assert path.variables["found2"] is True
        assert path.variables["notfound"] is True
