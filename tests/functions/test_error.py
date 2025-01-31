import unittest
import os
import json
from csvpath import CsvPaths
from csvpath.util.nos import Nos
from csvpath.util.file_readers import DataFileReader

PATH = "tests/test_resources/test.csv"


class TestFunctionsError(unittest.TestCase):
    def test_function_error_1(self):
        paths = CsvPaths()
        paths.paths_manager.add_named_paths(
            name="errors",
            paths=[
                f""" ~
            validation-mode:print, no-raise, no-stop
            error-mode:full
            ~
            ${PATH}[1*]
            [
                error("This is line: $.csvpath.line_number")
            ]"""
            ],
        )
        paths.file_manager.add_named_file(name="test_errors", path=PATH)
        paths.collect_paths(pathsname="errors", filename="test_errors")
        results = paths.results_manager.get_named_results("errors")
        assert results
        assert len(results) == 1
        result = results[0]
        assert result.has_errors()
        ps = result.printouts
        assert "default" in ps
        lst = ps["default"]
        assert len(lst) > 0
        assert lst[0].find("This is line:") > -1
        assert lst[0].find("test_errors:errors:0") > -1

    def test_function_error_2(self):
        paths = CsvPaths()
        paths.paths_manager.add_named_paths(
            name="errors",
            paths=[
                f"""~
            validation-mode:print, no-raise, no-stop
            error-mode:bare
            ~
            ${PATH}[1*] [
                error("This is line: $.csvpath.line_number")
            ]"""
            ],
        )
        paths.file_manager.add_named_file(name="test_errors", path=PATH)
        paths.collect_paths(pathsname="errors", filename="test_errors")
        results = paths.results_manager.get_named_results("errors")
        assert results
        assert len(results) == 1
        result = results[0]
        assert result.has_errors()
        ps = result.printouts
        assert "default" in ps
        lst = ps["default"]
        assert len(lst) > 0
        assert lst[0].find("This is line:") > -1
        assert lst[0].find("test_errors:errors:0") == -1

    def test_error_file(self):
        paths = CsvPaths()
        paths.paths_manager.add_named_paths(
            name="errors",
            paths=[
                f"""
            ~validation-mode:print, no-raise, no-stop~
            ${PATH}[1*]
            [
                print("$.csvpath.line_number")
                mod.nocontrib(line_number(), 2) == 0 -> add("five", none())
                true()
            ]"""
            ],
        )
        paths.file_manager.add_named_file(name="test_errors", path=PATH)
        paths.collect_paths(pathsname="errors", filename="test_errors")
        results = paths.results_manager.get_named_results("errors")
        assert results
        assert len(results) == 1
        result = results[0]
        assert result.has_errors()
        assert Nos(result.instance_dir).dir_exists()
        ef = os.path.join(result.instance_dir, "errors.json")
        assert Nos(ef).exists()
        with DataFileReader(ef) as file:
            j = json.load(file.source)
            assert len(j) == 8
