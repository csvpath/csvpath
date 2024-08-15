import unittest
from csvpath.csvpaths import CsvPaths

FILES = {
    "food": "tests/test_resources/named_files/food.csv",
    "test": "tests/test_resources/named_files/test.csv",
}
NAMED_PATHS_DIR = "tests/test_resources/named_paths/"


class TestNewCsvPaths(unittest.TestCase):
    def test_csvpaths_next_paths(self):
        print("")
        cs = CsvPaths()
        cs.files_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(NAMED_PATHS_DIR)
        cnt = 0
        for line in cs.next_paths("food", "food"):
            cnt += 1
        assert cnt == 4

    def test_csvpaths_fast_forward_paths(self):
        print("")
        cs = CsvPaths()
        cs.files_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(NAMED_PATHS_DIR)
        cs.fast_forward_paths("food", "food")
        n = cs.results_manager.get_number_of_results("food")
        valid = cs.results_manager.is_valid("food")
        assert not valid
        assert n == 2
        pvars = cs.results_manager.get_variables("food")
        assert "candy" in pvars
        assert isinstance(pvars["candy"], list)
        assert pvars["candy"] == [2, 7]

    def test_csvpaths_collect_paths(self):
        cs = CsvPaths()
        cs.files_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(NAMED_PATHS_DIR)
        cs.collect_paths("food", "food")
        valid = cs.results_manager.is_valid("food")
        assert not valid
        assert cs.results_manager.get_number_of_results("food") == 2
        pvars = cs.results_manager.get_variables("food")
        assert "candy" in pvars
        assert isinstance(pvars["candy"], list)
        assert pvars["candy"] == [2, 7]
