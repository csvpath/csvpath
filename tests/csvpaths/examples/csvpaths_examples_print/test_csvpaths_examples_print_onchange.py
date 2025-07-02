import unittest
import os
from csvpath import CsvPaths
from csvpath.util.file_readers import DataFileReader

FILE = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_print{os.sep}assets{os.sep}process-list-cols.csv"
PATH = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_print{os.sep}assets{os.sep}onchange.csvpath"
ONCE = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_print{os.sep}assets{os.sep}oncex.csvpath"


class TestCsvPathsExamplesPrint(unittest.TestCase):
    def test_print_onchange_1(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.file_manager.add_named_file(name="people", path=FILE)
        paths.paths_manager.add_named_paths_from_file(name="oc", file_path=PATH)
        paths.collect_paths(filename="people", pathsname="oc")
        results = paths.results_manager.get_named_results("oc")
        assert len(results) == 1
        assert len(results[0].lines) > 2  # don't know how many but much > 1
        printouts = results[0].get_printouts("default")
        assert len(printouts) > 2

    def test_print_once_1(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        print(f"inputs.files: {paths.config.config_path}")
        print(f"inputs.paths: {paths.config.get(section='inputs', name='csvpaths')}")
        print(f"inputs.paths: {paths.config.get(section='inputs', name='csvpaths')}")
        paths.file_manager.add_named_file(name="people", path=FILE)
        paths.paths_manager.add_named_paths_from_file(name="oncex", file_path=ONCE)
        paths.collect_paths(filename="people", pathsname="oncex")
        results = paths.results_manager.get_named_results("oncex")
        assert len(results) == 1
        assert len(results[0].lines) > 2  # don't know how many but much > 1
        printouts = results[0].get_printouts("once")
        assert len(printouts) == 1
        printouts = results[0].get_printouts("default")
        assert len(printouts) == 5
