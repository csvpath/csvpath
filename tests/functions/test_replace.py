import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = "tests/test_resources/test.csv"


class TestFunctionsReplace(unittest.TestCase):
    def test_function_replace1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1*]
            [
                yes()
                replace(0, count_lines())
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 8
        assert len(lines[0]) == 3
        assert lines[0] == [2, "Kermit", "hi!"]
        assert lines[1] == [3, "Bat", "blurgh..."]

    def test_function_replace2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1*]
            [
                yes()
                replace(0, count_lines())
                replace(1, concat(#1, ", a friendly animal"))
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 8
        assert len(lines[0]) == 3
        assert lines[0] == [2, "Kermit, a friendly animal", "hi!"]
        assert lines[1] == [3, "Bat, a friendly animal", "blurgh..."]

    def test_function_append(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                line_number.nocontrib() == 0 -> append("rnd_id", "rnd_id")
                above.nocontrib( line_number(), 0 ) -> append("rnd_id", shuffle())
                print_line()
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9
        assert len(lines[0]) == 4
        assert lines[0][3] == "rnd_id"
        assert path.matcher.line[3] is not None

    def test_function_append2(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*][
                line_number.nocontrib() == 0 -> append(3, "rnd_id")
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_append3(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*][
                line_number.nocontrib() == 0 -> append("rnd_id")
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()
