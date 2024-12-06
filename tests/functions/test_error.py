import unittest
import os
import json
from csvpath import CsvPaths

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
        assert os.path.exists(result.instance_dir)
        ef = os.path.join(result.instance_dir, "errors.json")
        assert os.path.exists(ef)
        with open(ef, "r", encoding="utf-8") as file:
            j = json.load(file)
            assert len(j) == 4
