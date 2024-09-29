import unittest
import pytest
from csvpath.csvpath import CsvPath
from tests.save import Save
from csvpath.matching.util.exceptions import ChildrenException

PATH = "tests/test_resources/test.csv"
EMPTY = "tests/test_resources/empty.csv"


class TestFunctionsFirstLine(unittest.TestCase):
    def test_function_firstline1(self):
        path = CsvPath()
        Save._save(path, "test_function_firstline1")
        path.parse(
            f"""
            ${PATH}[0-7]
            [
                regex(#say, /sniffle/)
                firstline.nocontrib() -> @line = count_lines()
                firstmatch.nocontrib() -> @match = count_lines()
                firstscan.nocontrib() -> @scan = count_lines()

            ]"""
        )
        lines = path.collect()
        print(f"\n test_function_firstline1: lines: {lines}")
        print(f"test_function_firstline1: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["line"] == 1
        assert path.variables["scan"] == 1
        assert path.variables["match"] == 5

    def test_function_firstline2(self):
        path = CsvPath()
        Save._save(path, "test_function_firstline2")
        path.parse(
            f"""
            ${PATH}[3-7]
            [
                regex(#say, /sniffle/)
                firstline.nocontrib() -> @line = count_lines()
                firstmatch.nocontrib() -> @match = count_lines()
                firstscan.nocontrib() -> @scan = count_lines()

            ]"""
        )
        lines = path.collect()
        print(f"\n test_function_firstline2: lines: {lines}")
        print(f"test_function_firstline2: path vars: {path.variables}")
        assert len(lines) == 1
        assert "line" not in path.variables
        assert path.variables["scan"] == 4
        assert path.variables["match"] == 5

    def test_function_firstline3(self):
        path = CsvPath()
        Save._save(path, "test_function_firstline3")
        path.parse(
            f"""
            ${PATH}[*]
            [
                firstscan.nocontrib() -> print("we scan the whole file from the 0th line")
                last.nocontrib() -> print("the file has $.csvpath.count_lines rows")
            ]"""
        )
        lines = path.collect()
        print(f"\n test_function_firstline3: lines: {lines}")
        print(f"test_function_firstline3: path vars: {path.variables}")
        assert len(lines) == 9

    def test_function_firstline4(self):
        path = CsvPath()
        Save._save(path, "test_function_firstline4")
        path.parse(
            f"""
            ${PATH}[*]
            [
                firstline.nocontrib(fail()) ->
                    print("we scan the whole file from the 0th line but are failing.")
            ]"""
        )
        lines = path.collect()
        print(f"\n test_function_firstline4: lines: {lines}")
        print(f"test_function_firstline4: path vars: {path.variables}")
        assert path.is_valid is False
        assert len(lines) == 9

    def test_function_firstline5(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["raise"]
        Save._save(path, "test_function_firstline5")
        with pytest.raises(ChildrenException):
            path.parse(
                f"""
                ${PATH}[*]
                [
                    firstline.nocontrib(@t == fail()) ->
                        print("we scan the whole file from the 0th line but are failing.")
                ]"""
            )
            lines = path.collect()
            print(f"\n test_function_firstline5: lines: {lines}")
