import unittest
from csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"
EMPTY = "tests/test_resources/empty.csv"


class TestFunctionsAny(unittest.TestCase):
    def test_function_any_function1(self):
        path = CsvPath()
        Save._save(path, "test_function_any_function1")
        path.parse(
            f"""
            ${PATH}[3]
            [
                @frog = any(headers(), "Frog")
            ]"""
        )
        lines = path.collect()
        print(f"\ntest_function_any_function: lines: {lines}")
        print(f"test_function_any_function: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["frog"] is True

    def test_function_any_function2(self):
        path = CsvPath()
        Save._save(path, "test_function_any_function2")
        path.parse(
            f"""
            ~ description: this is a test! ~
            ~ name: harry ~
            ~ fish: bluefish and bass temp: hot ~

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
        Save._save(path, "test_function_any_function3")
        path.parse(
            f"""
            ${PATH}[3]
            [
                @v = any(variables())
                @frog = any(headers(), "Frog")
                @found = any()
                @slug = any("slug")
                @bear = any(headers(),"Bear")
                @me = any("True")
                @h = any(headers())
                @v2 = any(variables())
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
        print(f"\ntest_function_any_function: lines: {lines}")
        print(f"test_function_any_function: path vars: {path.variables}")
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
        print(f"\ntest_function_any_function: lines: {lines}")
        print(f"test_function_any_function: path vars: {path.variables}")
        # assert len(lines) == 2
        assert path.variables["found"] is False
        assert path.variables["found2"] is True
        assert path.variables["notfound"] is True
