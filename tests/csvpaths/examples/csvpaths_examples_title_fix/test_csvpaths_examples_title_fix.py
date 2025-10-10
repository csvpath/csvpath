import unittest
import pytest
import os
from csvpath import CsvPaths
from csvpath.matching.util.exceptions import MatchException
from csvpath.util.file_readers import DataFileReader


class TestCsvPathsExamplesTitleFix(unittest.TestCase):
    def test_title_fix_1(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.config.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.file_manager.add_named_file(
            name="title_fix",
            path=f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_title_fix{os.sep}assets{os.sep}checkouts.csv",
        )
        paths.paths_manager.add_named_paths_from_file(
            name="title_fix",
            file_path=f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_title_fix{os.sep}assets{os.sep}title_fix.csvpaths",
        )
        paths.collect_paths(filename="title_fix", pathsname="title_fix")
        print("test_title_fix_1: collected paths")
        results = paths.results_manager.get_named_results("title_fix")
        print("test_title_fix_1: loaded results")
        assert len(results) == 1
        result = results[0]
        d = result.data_file_path
        with DataFileReader(d) as f:
            s = f.read()
            assert s.find("Great circle : a novel {os.sep} Maggie Shipstead") == -1

    def test_title_fix_2(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.config.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.file_manager.add_named_file(
            name="title_fix",
            path=f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_title_fix{os.sep}assets{os.sep}checkouts.csv",
        )
        paths.paths_manager.add_named_paths_from_file(
            name="title_fix_schema",
            file_path=f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_title_fix{os.sep}assets{os.sep}title_fix_schema_2.csvpaths",
        )
        #
        # blows up because [2019] is not an integer()
        #
        with pytest.raises(MatchException):
            paths.collect_paths(filename="title_fix", pathsname="title_fix_schema")
