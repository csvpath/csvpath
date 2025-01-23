import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = "tests/test_resources/test.csv"


class TestFunctionsSubstring(unittest.TestCase):
    def test_function_starts_with_1(self):
        path = (
            CsvPath()
            .parse(
                f"""${PATH}[*][
                @t1 = starts_with("# testtest", "#")
                @t2 = starts_with("! testtest", "#")
            ]"""
            )
            .fast_forward()
        )
        assert path.variables["t1"] is True
        assert path.variables["t2"] is False

    def test_function_startswith_2(self):
        path = (
            CsvPath()
            .parse(
                f"""${PATH}[*][
                @t1 = startswith("# testtest", "#")
                @t2 = startswith("! testtest", "#")
            ]"""
            )
            .fast_forward()
        )
        assert path.variables["t1"] is True
        assert path.variables["t2"] is False

    def test_function_startswith_3(self):
        path = (
            CsvPath()
            .parse(
                f"""${PATH}[*][
                @t1 = startswith(none(), "#")
                @t2 = startswith("! testtest", none())
            ]"""
            )
            .fast_forward()
        )
        assert path.variables["t1"] is False
        assert path.variables["t2"] is False

    def test_function_startswith_4(self):
        path = (
            CsvPath()
            .parse(
                f"""${PATH}[*][
                @t1 = startswith("vole", "")
                @t2 = startswith("", "vole")
            ]"""
            )
            .fast_forward()
        )
        assert path.variables["t1"] is False
        assert path.variables["t2"] is False

    def test_function_ends_with_1(self):
        path = (
            CsvPath()
            .parse(
                f"""${PATH}[*][
                @t1 = ends_with("# testtest", "est")
                @t2 = endswith("! testtest", "bat")
            ]"""
            )
            .fast_forward()
        )
        assert path.variables["t1"] is True
        assert path.variables["t2"] is False
