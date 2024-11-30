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
                ~
                fail() does not mean a line fails/doesn't fail/matches/doesn't match.
                it just indicates that a file is invalid. we may want to collect the
                line that caused the invalidation -- or not.
                ~
                fail()
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
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
        assert len(lines) == 1
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
        assert len(lines) == 1
        assert path.is_valid is True
        assert path.variables["valid"] is True
        assert path.variables["failed"] is False

    def test_function_fail_all1(self):
        path = CsvPath()

        path.parse(
            f"""
            ${PATH}[1]
            [
                fail()
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.is_valid is False
