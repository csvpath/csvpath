import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"
EMPTY = f"tests{os.sep}test_resources{os.sep}empty.csv"


class TestFunctionsFirstLine(unittest.TestCase):
    def test_function_firstline1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[0-7]
            [
                regex(/sniffle/, #say)
                firstline.nocontrib() -> @line = count_lines()
                firstmatch.nocontrib() -> @match = count_lines()
                firstscan.nocontrib() -> @scan = count_lines()

            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["line"] == 1
        assert path.variables["scan"] == 1
        assert path.variables["match"] == 5

    def test_function_firstline2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[3-7]
            [
                regex(/sniffle/, #say)
                firstline.nocontrib() -> @line = count_lines()
                firstmatch.nocontrib() -> @match = count_lines()
                firstscan.nocontrib() -> @scan = count_lines()

            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert "line" not in path.variables
        assert path.variables["scan"] == 4
        assert path.variables["match"] == 5

    def test_function_firstline3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                firstscan.nocontrib() -> print("we scan the whole file from the 0th line")
                last.nocontrib() -> print("the file has $.csvpath.count_lines rows")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_function_firstline4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                firstline.nocontrib(fail()) ->
                    print("we scan the whole file from the 0th line but are failing.")
            ]"""
        )
        lines = path.collect()
        assert path.is_valid is False
        assert len(lines) == 9

    def test_function_firstline5(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.collect(
                f""" ${PATH}[*][
                    firstline.nocontrib(@t == fail()) ->
                        print("we scan the whole file from the 0th line but are failing.")
                ]"""
            )
