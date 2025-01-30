import unittest
import os
import json
from csvpath import CsvPaths
from csvpath.util.nos import Nos
from csvpath.util.file_readers import DataFileReader

PATH = "tests/test_resources/test.csv"


class TestFunctionsError(unittest.TestCase):
    def test_function_error_file(self):
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
