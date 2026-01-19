import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
PATH2 = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test-5.csv"


class TestCsvPathFunctionsReplace(unittest.TestCase):
    def test_function_insert_1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                odd.nocontrib(line_number()) -> @day = "sunny"
                even.nocontrib(line_number()) -> @day = "cloudy"
                insert(1, "weather", @day)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9
        assert len(lines[0]) == 4
        assert len(lines[1]) == 4
        assert path.headers == ["firstname", "weather", "lastname", "say"]
        assert lines[0][1] == "weather"
        assert lines[1][1] == "sunny"
        assert lines[2][1] == "cloudy"

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

    def test_function_replace3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1*]
            [
                yes()
                replace(#firstname, count_lines())
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 8
        assert len(lines[0]) == 3
        assert lines[0] == [2, "Kermit", "hi!"]
        assert lines[1] == [3, "Bat", "blurgh..."]

    def test_function_replace4(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ checks that replace deals with blank and/or short lines. it had a problem at one point ~
            ${PATH2}[*]
            [
                replace(#2, "replaced")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 11
        lst = [_ for _ in lines if len(_) > 2 and _[2] == "replaced"]
        assert len(lst) == 10

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
        path = CsvPath().parse(
            f"""${PATH}[*][
                line_number.nocontrib() == 0 -> append(3, "rnd_id")
            ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_append3(self):
        path = CsvPath().parse(
            f"""${PATH}[*][
                line_number.nocontrib() == 0 -> append("rnd_id")
            ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.fast_forward()
