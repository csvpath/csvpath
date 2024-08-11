import unittest
from csvpath.csvpath import CsvPath

PATH = "tests/test_resources/test.csv"


class TestFunctionsFail(unittest.TestCase):
    def test_function_fail1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [
                fail()
            ]"""
        )
        lines = path.collect()
        print(f"\test_function_fail1: lines: {lines}")
        assert len(lines) == 0
        assert path.is_valid is False

    def test_function_fail12(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [
                yes()
            ]"""
        )
        lines = path.collect()
        print(f"\test_function_fail2: lines: {lines}")
        assert len(lines) == 1
        assert path.is_valid is True

    def test_function_fail3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [
                fail()
                @valid = valid()
                @failed = failed()
            ]"""
        )
        lines = path.collect()
        print(f"test_function_fail3: lines: {lines}")
        print(f"test_function_fail3: variables: {path.variables}")
        assert len(lines) == 0
        assert path.is_valid is False
        assert path.variables["valid"] is False
        assert path.variables["failed"] is True

    def test_function_fail4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [
                yes()
                @valid = valid()
                @failed = failed()
            ]"""
        )
        lines = path.collect()
        print(f"test_function_fail4: lines: {lines}")
        print(f"test_function_fail4: variables: {path.variables}")
        assert len(lines) == 1
        assert path.is_valid is True
        assert path.variables["valid"] is True
        assert path.variables["failed"] is False
