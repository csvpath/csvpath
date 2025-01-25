import unittest
import os
from csvpath import CsvPaths


class TestTitleFix(unittest.TestCase):
    def test_title_fix_1(self):
        paths = CsvPaths()
        paths.file_manager.add_named_file(
            name="title_fix", path="tests/examples/title_fix/assets/checkouts.csv"
        )
        paths.paths_manager.add_named_paths_from_file(
            name="title_fix",
            file_path="tests/examples/title_fix/assets/title_fix.csvpaths",
        )
        paths.collect_paths(filename="title_fix", pathsname="title_fix")
        results = paths.results_manager.get_named_results("title_fix")
        assert len(results) == 1
        result = results[0]
        d = result.data_file_path
        with open(d, "r", encoding="utf-8") as file:
            s = file.read()
            assert s.find("Great circle : a novel / Maggie Shipstead") == -1

    def test_title_fix_2(self):
        print("")
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "collect, print")
        paths.file_manager.add_named_file(
            name="title_fix", path="tests/examples/title_fix/assets/checkouts.csv"
        )
        paths.paths_manager.add_named_paths_from_file(
            name="title_fix_schema",
            file_path="tests/examples/title_fix/assets/title_fix_schema.csvpaths",
        )
        paths.collect_paths(filename="title_fix", pathsname="title_fix_schema")
        results = paths.results_manager.get_named_results("title_fix_schema")
        assert len(results) == 1
