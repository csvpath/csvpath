import unittest
from csvpath.csvpath import CsvPath

PATH = "tests/test_resources/test.csv"


class TestFunctionsAdd(unittest.TestCase):
    def test_function_add1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = add( 4, length("this")) ]"""
        )
        lines = path.collect()
        print(f"test_function_add: lines: {lines}")
        print(f"test_function_add: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == 8

    def test_function_add2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = add( count(), length("this") ) ]"""
        )
        lines = path.collect()
        print(f"test_function_add: lines: {lines}")
        print(f"test_function_add: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == 5

    def test_function_add3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = add( count(), length("this"), 5 ) ]"""
        )
        lines = path.collect()
        print(f"test_function_add: lines: {lines}")
        print(f"test_function_add: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == 10

    def test_function_add4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = add( count(), length("this"), 5, 5 ) ]"""
        )
        lines = path.collect()
        print(f"test_function_add: lines: {lines}")
        print(f"test_function_add: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == 15
