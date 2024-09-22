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
        paths.file_manager.set_named_files(FILES)
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

    def test_csvpaths_stop_all_by_line(self):
        cs = CsvPaths()
        cs.file_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        i = 0
        for line in cs.next_by_line(filename="food", pathsname="stopping2"):
            print(f"test_csvpaths_stop_all_by_line: lines[{i}]: {line}")
            i += 1
        cs.results_manager.get_named_results("stopping2")
        vs = cs.results_manager.get_variables("stopping2")
        print(f"test_csvpaths_stop_all_by_line: stopping vs: {vs}")
        assert i == 3
        assert vs["one"] == [0, 1, 2]
        assert vs["two"] == [0, 1, 2]

    def test_csvpaths_stop_all_paths(self):
        cs = CsvPaths()
        cs.file_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        i = 0
        for line in cs.next_paths(filename="food", pathsname="stopping2"):
            print(f"test_csvpaths_stop_all_by_line: lines[{i}]: {line}")
            i += 1
        cs.results_manager.get_named_results("stopping2")
        vs = cs.results_manager.get_variables("stopping2")
        print(f"test_csvpaths_stop_all_by_line: stopping vs: {vs}")
        assert i == 3
        assert vs["one"] == [0, 1, 2]

    def test_csvpaths_fail_all_by_line(self):
        cs = CsvPaths()
        cs.file_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        i = 0
        for line in cs.next_by_line(filename="food", pathsname="failing"):
            print(f"test_csvpaths_fail_all_by_line: lines[{i}]: {line}")
            i += 1
        results = cs.results_manager.get_named_results("failing")
        print(f"test_csvpaths_fail_all_by_line: stopping results: {results}")
        assert len(results) == 2
        assert i == 11
        assert results[0].is_valid is False
        assert results[1].is_valid is False

    def test_csvpaths_fail_all_paths(self):
        cs = CsvPaths()
        cs.file_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        i = 0
        for line in cs.next_paths(filename="food", pathsname="failing"):
            print(f"test_csvpaths_fail_all_paths: lines[{i}]: {line}")
            i += 1
        results = cs.results_manager.get_named_results("failing")
        print(f"test_csvpaths_fail_all_paths: stopping results: {results}")
        assert len(results) == 2
        assert i == 22
        assert results[0].is_valid is False
        assert results[1].is_valid is False

    def test_csvpaths_skip_all_by_line_baseline(self):
        #
        # this test is the proof of the expected behavior without skip_all()
        #
        cs = CsvPaths()
        cs.file_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        i = 0
        for line in cs.next_by_line(
            filename="food", pathsname="skipping_baseline", collect=True
        ):
            i += 1
        assert i == 11
        results = cs.results_manager.get_named_results("skipping_baseline")
        assert len(results) == 2
        assert results[0].csvpath.variables["one"] == [0, 1, 2, 3, 6, 7, 8, 9, 10]
        assert results[1].csvpath.variables["two"] == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        assert cs.results_manager.get_variables("skipping_baseline")["one"] == [
            0,
            1,
            2,
            3,
            6,
            7,
            8,
            9,
            10,
        ]
        assert cs.results_manager.get_variables("skipping_baseline")["two"] == [
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
        ]

    def test_csvpaths_skip_all_by_line(self):
        cs = CsvPaths()
        cs.file_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        i = 0
        for line in cs.next_by_line(
            filename="food", pathsname="skipping", collect=True
        ):
            i += 1
        assert i == 9
        results = cs.results_manager.get_named_results("skipping")
        assert len(results) == 2
        assert results[0].csvpath.variables["one"] == [0, 1, 2, 3, 6, 7, 8, 9, 10]
        assert results[1].csvpath.variables["two"] == [0, 1, 2, 3, 6, 7, 8, 9, 10]
        assert cs.results_manager.get_variables("skipping")["one"] == [
            0,
            1,
            2,
            3,
            6,
            7,
            8,
            9,
            10,
        ]
        assert cs.results_manager.get_variables("skipping")["two"] == [
            0,
            1,
            2,
            3,
            6,
            7,
            8,
            9,
            10,
        ]

    def test_csvpaths_skip_all_paths(self):
        #
        # skip_all() is not usable in serial runs (_paths methods)
        # it does the same as skip()
        #
        cs = CsvPaths()
        cs.file_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        i = 0
        for line in cs.next_paths(filename="food", pathsname="skipping", collect=True):
            print(f"test_csvpaths_skip_all_paths: lines[{i}]: {line}")
            i += 1
        results = cs.results_manager.get_named_results("skipping")
        print(f"test_csvpaths_skip_all_paths: stopping results: {results}")
        assert len(results) == 2
        assert i == 20
        results = cs.results_manager.get_named_results("skipping")
        assert len(results) == 2
        assert results[0].csvpath.variables["one"] == [0, 1, 2, 3, 6, 7, 8, 9, 10]
        assert results[1].csvpath.variables["two"] == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        assert cs.results_manager.get_variables("skipping")["one"] == [
            0,
            1,
            2,
            3,
            6,
            7,
            8,
            9,
            10,
        ]
        assert cs.results_manager.get_variables("skipping")["two"] == [
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
        ]

    """

    def test_csvpaths_skip_all_paths(self):
        print("")
        cs = CsvPaths()
        cs.file_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.fast_forward_paths(filename="food", pathsname="food")

    def test_csvpaths_skip_all_by_line(self):
        print("")
        cs = CsvPaths()
        cs.file_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.fast_forward_paths(filename="food", pathsname="food")

    def test_csvpaths_advance_all_paths(self):
        print("")
        cs = CsvPaths()
        cs.file_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.fast_forward_paths(filename="food", pathsname="food")

    def test_csvpaths_advance_all_by_line(self):
        print("")
        cs = CsvPaths()
        cs.file_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.fast_forward_paths(filename="food", pathsname="food")
    """