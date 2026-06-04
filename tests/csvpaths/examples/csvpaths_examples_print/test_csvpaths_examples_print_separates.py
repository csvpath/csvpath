import unittest
import os
from csvpath import CsvPaths
from csvpath.util.nos import Nos
from csvpath.util.file_readers import DataFileReader

FILE = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_print{os.sep}assets{os.sep}process-list-cols.csv"
PATH1 = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_print{os.sep}assets{os.sep}separates.csvpath"
PATH2 = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_print{os.sep}assets{os.sep}onchange.csvpath"


class TestCsvPathsExamplesPrintSeparates(unittest.TestCase):
    def test_print_separates_1(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.config.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.file_manager.add_named_file(name="people", path=FILE)
        paths.paths_manager.add_named_paths_from_file(name="oc", file_path=PATH1)
        paths.collect_paths(filename="people", pathsname="oc")
        results = paths.results_manager.get_named_results("oc")
        assert len(results) == 1
        default = results[0].get_printouts("default")
        xy = results[0].get_printouts("FULL_XY values")
        assert len(default) > 2
        assert len(xy) == len(default)

        path = results[0].instance_dir

        nos = Nos(path)
        nos.path = nos.join("default.txt")
        assert nos.exists()
        with DataFileReader(nos.path) as file:
            _ = file.source.read()
            assert _.find("The city is SRC_NAM_TX") > -1

        nos = Nos(path)
        nos.path = nos.join("FULL_XY values.txt")
        assert nos.exists()
        with DataFileReader(nos.path) as file:
            _ = file.source.read()
            assert _.find("FULL_XY: Intake Care") > -1

    def test_print_separates_2(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.config.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.file_manager.add_named_file(name="people", path=FILE)
        paths.paths_manager.add_named_paths_from_file(name="oc", file_path=PATH2)
        paths.collect_paths(filename="people", pathsname="oc")
        results = paths.results_manager.get_named_results("oc")
        assert len(results) == 1
        path = results[0].instance_dir

        nos = Nos(path)
        nos.path = nos.join("default.txt")
        assert not nos.exists()
        nos = Nos(path)
        nos.path = nos.join("printouts.txt")
        assert nos.exists()
