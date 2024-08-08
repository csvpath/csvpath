import unittest
from csvpath.csvpath import CsvPath

PATH = "tests/test_resources/test.csv"
EMPTY = "tests/test_resources/empty.csv"


class TestFunctionsAny(unittest.TestCase):
    def test_function_any_function1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[3]
            [
                @frog = any(header(), "Frog")
            ]"""
        )
        lines = path.collect()
        print(f"\ntest_function_any_function: lines: {lines}")
        print(f"test_function_any_function: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["frog"] is True

    def test_function_any_function2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[3]
            [
                @found = any()
            ]"""
        )
        lines = path.collect()
        print(f"\ntest_function_any_function: lines: {lines}")
        print(f"test_function_any_function: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["found"] is True

    def test_function_any_function3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[3]
            [
                @v = any(variable())
                @frog = any(header(), "Frog")
                @found = any()
                @slug = any("slug")
                @bear = any(header(),"Bear")
                @me = any("True")
                @h = any(header())
                @v2 = any(variable())
            ]"""
        )
        lines = path.collect()
        print(f"\ntest_function_any_function: lines: {lines}")
        print(f"test_function_any_function: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["frog"] is True
        assert path.variables["found"] is True
        assert path.variables["slug"] is False
        assert path.variables["bear"] is False
        assert path.variables["v"] is False
        assert path.variables["v2"] is True
        assert path.variables["h"] is True

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
