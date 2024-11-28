import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = "tests/test_resources/test.csv"


class TestFunctionsSubstring(unittest.TestCase):
    def test_function_substring1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*][
                @s = substring("testtest", 4)
            ]"""
        )
        path.fast_forward()
        assert path.variables["s"] == "test"

    def test_function_substring2(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["raise"]
        path.parse(
            f"""
            ${PATH}[*][
                @s = substring("testtest", "no way!")
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_substring3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*][
                @s = substring("testtest", 40)
            ]"""
        )
        path.fast_forward()
        assert path.variables["s"] == "testtest"

    def test_function_substring4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*][
                @s = substring("", 0)
            ]"""
        )
        path.fast_forward()
        assert path.variables["s"] == ""

    def test_function_substring5(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["raise"]
        path.parse(
            f"""
            ${PATH}[*][
                @s = substring("abcd", -2)
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_startswith(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @t1 = starts_with("# testtest", "#")
                @t2 = starts_with("! testtest", "#")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9
        assert path.variables["t1"] is True
        assert path.variables["t2"] is False
