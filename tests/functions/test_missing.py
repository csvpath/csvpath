import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"
EMPTY = "tests/test_resources/empty.csv"
FOOD = "tests/test_resources/food.csv"


class TestFunctionsMissing(unittest.TestCase):
    def test_function_missing1(self):
        path = CsvPath()
        Save._save(path, "test_function_missing1")
        path.parse(
            f"""
            ${PATH}[3]
            [
               ~ missing() ~
               @a.asbool = missing()
            ]"""
        )
        lines = path.collect()
        print(f"\test_function_missing1: lines: {lines}")
        print(f"test_function_missing1: path vars: {path.variables}")
        assert len(lines) == 0
        assert path.variables["a"] is False

    def test_function_missing2(self):
        print("")
        path = CsvPath()
        Save._save(path, "test_function_missing2")
        path.parse(
            f"""
            ${EMPTY}[1*]
            [
               @a.asbool = missing()
               print("all.asbool: $.variables.a  $.csvpath.line_number")
            ]"""
        )
        lines = path.collect()
        print(f"\n test_function_missing2: lines: {lines}")
        print(f"test_function_missing2: path vars: {path.variables}")
        assert len(lines) == 3
        assert path.variables["a"] is True

    def test_function_missing3(self):
        path = CsvPath()
        Save._save(path, "test_function_missing3")
        path.parse(
            f"""
            ${FOOD}[10]
            [
               missing()
            ]"""
        )
        lines = path.collect()
        print(f"\n test_function_missing3: lines: {lines}")
        print(f"test_function_missing3: path vars: {path.variables}")
        assert len(lines) == 1

    def test_function_missing4(self):
        path = CsvPath()
        Save._save(path, "test_function_missing4")
        path.parse(
            f"""
            ${FOOD}[10]
            [
               missing(#food,#type,#year)
            ]"""
        )
        lines = path.collect()
        print(f"\n test_function_missing4: lines: {lines}")
        print(f"test_function_missing4: path vars: {path.variables}")
        assert len(lines) == 1

    def test_function_missing5(self):
        path = CsvPath()
        Save._save(path, "test_function_missing5")
        path.parse(
            f"""
            ${FOOD}[*]
            [
               not(missing(headers()))
            ]"""
        )
        lines = path.collect()
        print(f"\n test_function_missing5: lines: {lines}")
        print(f"test_function_missing5: path vars: {path.variables}")
        assert len(lines) == 10

    def test_function_missing6(self):
        path = CsvPath()
        Save._save(path, "test_function_missing6")
        path.parse(
            f"""
            ${FOOD}[*]
            [
                ~ we have 10 lines of no vars and 1 line of a missing var that is not()ed ~
                last.nocontrib() -> @noway = none()
                not(missing( variables()))
            ]"""
        )
        lines = path.collect()
        print(f"\n test_function_missing6: lines: {lines}")
        print(f"test_function_missing6: path vars: {path.variables}")
        assert len(lines) == 11

    def test_function_missing7(self):
        path = CsvPath()
        Save._save(path, "test_function_missing7")
        path.parse(
            f"""
            ${FOOD}[*]
            [
                ~ we have 10 lines of no vars and 1 line of a missing var that is not()ed ~
                last.nocontrib() -> @noway = none()
                missing( variables())
            ]"""
        )
        lines = path.collect()
        print(f"\n test_function_missing7: lines: {lines}")
        print(f"test_function_missing7: path vars: {path.variables}")
        assert len(lines) == 1
