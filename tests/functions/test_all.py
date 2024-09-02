import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"
EMPTY = "tests/test_resources/empty.csv"
FOOD = "tests/test_resources/food.csv"


class TestFunctionsAll(unittest.TestCase):
    def test_function_all1(self):
        path = CsvPath()
        Save._save(path, "test_function_all1")
        path.parse(
            f"""
            ${PATH}[3]
            [
               @a = all()
            ]"""
        )
        lines = path.collect()
        print(f"\test_function_all1: lines: {lines}")
        print(f"test_function_all1: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["a"] is True

    def test_function_all2(self):
        path = CsvPath()
        Save._save(path, "test_function_all2")
        path.parse(
            f"""
            ${EMPTY}[1*]
            [
               @a.asbool = all()
            ]"""
        )
        lines = path.collect()
        print(f"\ntest_function_all2: lines: {lines}")
        print(f"test_function_all2: path vars: {path.variables}")
        assert len(lines) == 0
        assert path.variables["a"] is False

    def test_function_all3(self):
        path = CsvPath()
        Save._save(path, "test_function_all3")
        path.parse(
            f"""
            ${FOOD}[10]
            [
               all()
            ]"""
        )
        lines = path.collect()
        print(f"\test_function_all3: lines: {lines}")
        print(f"test_function_all3: path vars: {path.variables}")
        assert len(lines) == 0

    def test_function_all4(self):
        path = CsvPath()
        Save._save(path, "test_function_all4")
        path.parse(
            f"""
            ${FOOD}[10]
            [
               all(#food,#type,#units)
            ]"""
        )
        lines = path.collect()
        print(f"\test_function_all4: lines: {lines}")
        print(f"test_function_all4: path vars: {path.variables}")
        assert len(lines) == 1

    def test_function_all5(self):
        path = CsvPath()
        Save._save(path, "test_function_all5")
        path.parse(
            f"""
            ${FOOD}[*]
            [
               not(all(headers()))
            ]"""
        )
        lines = path.collect()
        print(f"\test_function_all5: lines: {lines}")
        print(f"test_function_all5: path vars: {path.variables}")
        assert len(lines) == 1

    def test_function_all6(self):
        path = CsvPath()
        Save._save(path, "test_function_all6")
        path.parse(
            f"""
            ${FOOD}[*]
            [
                last.nocontrib() -> @noway = none()
                not(all( variables()))
            ]"""
        )
        lines = path.collect()
        print(f"\n test_function_all6: lines: {lines}")
        print(f"test_function_all6: path vars: {path.variables}")
        assert len(lines) == 1
