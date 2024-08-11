import unittest
from csvpath.csvpath import CsvPath

PATH = "tests/test_resources/test.csv"
EMPTY = "tests/test_resources/empty.csv"
FOOD = "tests/test_resources/food.csv"


class TestFunctionsAll(unittest.TestCase):
    def test_function_all1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[3]
            [
               @a = all()
            ]"""
        )
        lines = path.collect()
        print(f"\ntest_function_any_function: lines: {lines}")
        print(f"test_function_any_function: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["a"] is True

    def test_function_all2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${EMPTY}[1*]
            [
               @a.asbool = all()
               ~all()~
            ]"""
        )
        lines = path.collect()
        print(f"\test_function_all2: lines: {lines}")
        print(f"test_function_all2: path vars: {path.variables}")
        assert len(lines) == 0
        assert path.variables["a"] is False

    def test_function_all3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${FOOD}[10]
            [
               all()
            ]"""
        )
        lines = path.collect()
        print(f"\ntest_function_any_function: lines: {lines}")
        print(f"test_function_any_function: path vars: {path.variables}")
        assert len(lines) == 0

    def test_function_all4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${FOOD}[10]
            [
               all(#food,#type,#units)
            ]"""
        )
        lines = path.collect()
        print(f"\ntest_function_any_function: lines: {lines}")
        print(f"test_function_any_function: path vars: {path.variables}")
        assert len(lines) == 1
