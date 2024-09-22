import unittest
from csvpath import CsvPaths
from csvpath.util.line_monitor import LineMonitor

FILES = {
    "food": "tests/test_resources/named_files/food.csv",
    "test": "tests/test_resources/named_files/test.csv",
}
NAMED_PATHS_DIR = "tests/test_resources/named_paths/"


class TestCsvPathsCoordinatorFunctions(unittest.TestCase):
    def test_csvpaths_line_numbers_and_headers(self):
        print("")
        paths = CsvPaths()
        paths.files_manager.set_named_files(FILES)
        paths.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        paths.fast_forward_paths(filename="food", pathsname="food")
        # all we need to see is that the new object has the data/objects
        # and that they are separate
        path = paths.csvpath()
        path.parse("$food[*][yes()]")
        assert path.line_monitor is not None
        assert path.line_monitor.physical_end_line_number == 10
        assert path.headers is not None
        assert len(path.headers) == 5
        path.line_monitor.next_line(last_line=["test"], data=["test"])
        assert path.line_monitor.physical_line_count == 1
        path2 = paths.csvpath()
        path2.parse("$food[*][yes()]")
        path2.headers[0] = "fish"
        assert path.headers[0] != "fish"
        assert path2.line_monitor.physical_line_count is None

    """
    def test_csvpaths_stop_all_paths(self):
        print("")
        path = CsvPaths()
        path.files_manager.set_named_files(FILES)
        path.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        path.fast_forward_paths(filename="food", pathsname="stopping")

    def test_csvpaths_stop_all_by_line(self):
        print("")
        cs = CsvPaths()
        cs.files_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.fast_forward_paths(filename="food", pathsname="food")

    def test_csvpaths_fail_all_paths(self):
        print("")
        cs = CsvPaths()
        cs.files_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.fast_forward_paths(filename="food", pathsname="food")

    def test_csvpaths_fail_all_by_line(self):
        print("")
        cs = CsvPaths()
        cs.files_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.fast_forward_paths(filename="food", pathsname="food")

    def test_csvpaths_skip_all_paths(self):
        print("")
        cs = CsvPaths()
        cs.files_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.fast_forward_paths(filename="food", pathsname="food")

    def test_csvpaths_skip_all_by_line(self):
        print("")
        cs = CsvPaths()
        cs.files_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.fast_forward_paths(filename="food", pathsname="food")

    def test_csvpaths_advance_all_paths(self):
        print("")
        cs = CsvPaths()
        cs.files_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.fast_forward_paths(filename="food", pathsname="food")

    def test_csvpaths_advance_all_by_line(self):
        print("")
        cs = CsvPaths()
        cs.files_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.fast_forward_paths(filename="food", pathsname="food")
    """
