import unittest
import pytest
import os
from csvpath import CsvPaths
from csvpath.matching.util.exceptions import MatchException

CATEGORIES_DATA = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_cli{os.sep}assets{os.sep}categories.csv"
CATEGORIES_PATH = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_cli{os.sep}assets{os.sep}categories.csvpath"
PURCHASES_DATA = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_cli{os.sep}assets{os.sep}january-2025.csv"
PURCHASES_PATH_NO_RUN = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_cli{os.sep}assets{os.sep}purchases-no-run.csvpath"
PURCHASES_PATH = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_cli{os.sep}assets{os.sep}purchases.csvpath"


class TestCsvPathsExamplesCli(unittest.TestCase):
    def test_cli_example_1(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.file_manager.add_named_file(name="purchases", path=PURCHASES_DATA)
        paths.paths_manager.add_named_paths_from_file(
            name="purchases", file_path=PURCHASES_PATH_NO_RUN
        )
        paths.collect_paths(filename="purchases", pathsname="purchases")
        results = paths.results_manager.get_named_results("purchases")
        #
        # all we need to know is:
        #   1) did it blow up because trying to save a no-run csvpath, and
        #   2) did we end up with just 1 result
        #
        assert len(results) == 1

    def test_cli_example_2(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpath", "collect, print")
        paths.add_to_config("errors", "csvpaths", "collect, print")
        paths.file_manager.add_named_file(name="purchases", path=PURCHASES_DATA)
        paths.paths_manager.add_named_paths_from_file(
            name="purchases", file_path=PURCHASES_PATH
        )
        paths.collect_paths(filename="purchases", pathsname="purchases")
        results = paths.results_manager.get_named_results("purchases")
        #
        # we need to know:
        #  - 0 and 1 ran ok
        #  - 2, the lookup failed because we haven't run the lookup named-paths yet
        #
        assert len(results) == 3
        assert results[2].errors_count > 0

    def test_cli_example_3(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.config.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.file_manager.add_named_file(name="categories", path=CATEGORIES_DATA)
        paths.paths_manager.add_named_paths_from_file(
            name="categories", file_path=CATEGORIES_PATH
        )
        paths.collect_paths(filename="categories", pathsname="categories")
        #
        # we could in principle use the existing, but we don't specifically test for
        # reuse, so its better to treat them as single-use when that is an option.
        #
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.config.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.file_manager.add_named_file(name="purchases", path=PURCHASES_DATA)
        paths.paths_manager.add_named_paths_from_file(
            name="purchases", file_path=PURCHASES_PATH
        )
        paths.collect_paths(filename="purchases", pathsname="purchases")
        results = paths.results_manager.get_named_results("purchases")
        #
        # we need to know:
        #  - all ran fine
        #
        assert len(results) == 3
        assert results[2].errors_count == 0
