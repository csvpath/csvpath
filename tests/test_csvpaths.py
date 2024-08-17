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
            print(f"test_csvpaths_next_paths: path: {line[len(line) - 1]}")
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

    # ================= breadth first ==================

    def test_csvpaths_next_by_line(self):
        cs = CsvPaths()
        cs.files_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(NAMED_PATHS_DIR)
        cnt = 0
        for line in cs.next_by_line(filename="food", pathsname="many"):
            cnt += 1
            print(f"vars 0: {cs.current_matchers[0].variables}")
            print(f"vars 1: {cs.current_matchers[1].variables}")
            assert (
                cs.current_matchers[0].variables["test"]
                != cs.current_matchers[1].variables["test"]
            )
        assert cnt == 11
        valid = cs.results_manager.is_valid("many")
        assert valid
        assert cs.results_manager.get_number_of_results("many") == 2
        pvars = cs.results_manager.get_variables("many")
        assert "one" in pvars
        assert isinstance(pvars["one"], int)
        assert pvars["one"] == 11
