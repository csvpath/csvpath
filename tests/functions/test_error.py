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
        print(f"test_function_error_file: instance_dir: {result.instance_dir}")
        assert Nos(result.instance_dir).dir_exists()
        # assert os.path.exists(result.instance_dir)
        ef = os.path.join(result.instance_dir, "errors.json")
        print(f"test_function_error_file: ef: {ef}")
        assert Nos(ef).exists()
        # assert os.path.exists(ef)
        with DataFileReader(ef) as file:
            # with open(ef, "r", encoding="utf-8") as file:
            j = json.load(file.source)
            assert len(j) == 4
