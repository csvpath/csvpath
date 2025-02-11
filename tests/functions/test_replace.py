import unittest
import pytest
import os
from csvpath import CsvPath, CsvPaths
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"


class TestFunctionsReplace(unittest.TestCase):
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

    def test_function_insert_2(self):
        paths = CsvPaths()
        np = f"tests{os.sep}test_resources{os.sep}named_paths{os.sep}insert.csvpath"

        paths.paths_manager.add_named_paths_from_file(name="insert", file_path=np)
        paths.file_manager.add_named_file(name="insert", path=PATH)
        paths.collect_paths(pathsname="insert", filename="insert")
        results = paths.results_manager.get_named_results("insert")

        assert len(results) == 2
        result = results[1]
        assert len(result) == 8

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
