import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsSubtract(unittest.TestCase):
    def test_function_subtract(self):
        path = CsvPath()
        Save._save(path, "test_function_subtract")
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = subtract( count(), length("this") ) ]"""
        )
        lines = path.collect()
        print(f"test_function_subtract: lines: {lines}")
        print(f"test_function_subtract: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == -3

    def test_function_subtract2(self):
        path = CsvPath()
        Save._save(path, "test_function_subtract2")
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = subtract( 10, count(), length("this") ) ]"""
        )
        lines = path.collect()
        print(f"test_function_subtract2: lines: {lines}")
        print(f"test_function_subtract2: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == 5

    def test_function_subtract3(self):
        path = CsvPath()
        Save._save(path, "test_function_subtract3")
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = subtract( 10, count(), length("this"), add( 2, 3) ) ]"""
        )
        lines = path.collect()
        print(f"test_function_subtract3: lines: {lines}")
        print(f"test_function_subtract3: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == 0
