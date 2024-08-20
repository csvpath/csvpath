import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsDivide(unittest.TestCase):
    def test_function_divide(self):
        path = CsvPath()
        Save._save(path, "test_function_divide")
        path.parse(
            f"""
            ${PATH}[2]
            [ @l = divide( 100, 10 ) ]"""
        )
        lines = path.collect()
        print(f"test_function_divide: lines: {lines}")
        print(f"test_function_divide: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == 10

    def test_function_divide2(self):
        path = CsvPath()
        Save._save(path, "test_function_divide2")
        path.parse(
            f"""
            ${PATH}[2-3]
            [ @l = divide( 100, count() ) ]"""
        )
        lines = path.collect()
        print(f"test_function_divide2: lines: {lines}")
        print(f"test_function_divide2: path vars: {path.variables}")
        assert len(lines) == 2
        assert path.variables["l"] == 50

    def test_function_divide3(self):
        path = CsvPath()
        Save._save(path, "test_function_divide3")
        path.parse(
            f"""
            ${PATH}[2-3]
            [ @l = divide( 100, count(), add(2,3) ) ]"""
        )
        lines = path.collect()
        print(f"test_function_divide3: lines: {lines}")
        print(f"test_function_divide3: path vars: {path.variables}")
        assert len(lines) == 2
        assert path.variables["l"] == 10

    def test_function_divide4(self):
        path = CsvPath()
        Save._save(path, "test_function_divide4")
        path.parse(
            f"""
            ${PATH}[2-3]
            [ @l = divide( 100, 0 ) ]"""
        )
        lines = path.collect()
        print(f"test_function_divide4: lines: {lines}")
        print(f"test_function_divide4: path vars: {path.variables}")
        assert len(lines) == 2
        import math

        assert math.isnan(path.variables["l"])
