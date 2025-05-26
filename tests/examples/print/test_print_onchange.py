import unittest
import os
from csvpath import CsvPaths
from csvpath.util.file_readers import DataFileReader


class TestRefs(unittest.TestCase):
    def test_print_onchange_1(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.file_manager.add_named_file(
            name="people",
            path=f"tests{os.sep}examples{os.sep}print{os.sep}assets{os.sep}process-list-cols.csv",
        )
        paths.paths_manager.add_named_paths_from_file(
            name="sourcemode",
            file_path=f"tests{os.sep}examples{os.sep}print{os.sep}assets{os.sep}onchange.csvpath",
        )
        paths.collect_paths(filename="people", pathsname="sourcemode")
        results = paths.results_manager.get_named_results("sourcemode")
        assert len(results) == 1
        assert len(results[0].lines) > 2  # don't know how many but much > 1
        printouts = results[0].get_printouts("default")
        assert len(printouts) > 2

    def test_print_once_1(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.file_manager.add_named_file(
            name="people",
            path=f"tests{os.sep}examples{os.sep}print{os.sep}assets{os.sep}process-list-cols.csv",
        )
        paths.paths_manager.add_named_paths_from_file(
            name="sourcemode",
            file_path=f"tests{os.sep}examples{os.sep}print{os.sep}assets{os.sep}once.csvpath",
        )
        paths.collect_paths(filename="people", pathsname="sourcemode")
        results = paths.results_manager.get_named_results("sourcemode")
        assert len(results) == 1
        assert len(results[0].lines) > 2  # don't know how many but much > 1
        printouts = results[0].get_printouts("once")
        assert len(printouts) == 1
        printouts = results[0].get_printouts("default")
        assert len(printouts) == 5
