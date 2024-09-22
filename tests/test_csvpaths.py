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
        cs.file_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cnt = 0
        for line in cs.next_paths(filename="food", pathsname="food"):
            print(f"test_csvpaths_next_paths: path: {line[len(line) - 1]}")
            cnt += 1
        assert cnt == 4

    def test_csvpaths_fast_forward_paths(self):
        print("")
        cs = CsvPaths()
        cs.file_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.fast_forward_paths(filename="food", pathsname="food")
        n = cs.results_manager.get_number_of_results("food")
        valid = cs.results_manager.is_valid("food")
        assert not valid
        assert n == 2
        pvars = cs.results_manager.get_variables("food")
        assert "candy" in pvars
        assert isinstance(pvars["candy"], list)
        assert pvars["candy"] == [3, 8]

    def test_csvpaths_collect_paths(self):
        cs = CsvPaths()
        cs.file_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.collect_paths(filename="food", pathsname="food")
        valid = cs.results_manager.is_valid("food")
        assert not valid
        assert cs.results_manager.get_number_of_results("food") == 2
        pvars = cs.results_manager.get_variables("food")
        assert "candy" in pvars
        assert isinstance(pvars["candy"], list)
        assert pvars["candy"] == [3, 8]

    # ================= breadth first ==================

    def test_csvpaths_next_by_line(self):
        cs = CsvPaths()
        cs.file_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cnt = 0
        for line in cs.next_by_line(filename="food", pathsname="many"):
            cnt += 1
            print(f"vars 0: {cs.current_matcher.variables}")
        assert cnt == 11
        valid = cs.results_manager.is_valid("many")
        assert valid
        assert cs.results_manager.get_number_of_results("many") == 2
        pvars = cs.results_manager.get_variables("many")
        assert "one" in pvars
        assert isinstance(pvars["one"], int)
        assert pvars["one"] == 11

    def test_csvpaths_metadata1(self):
        cs = CsvPaths()
        cs.file_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.fast_forward_by_line(filename="food", pathsname="many")
        meta = cs.results_manager.get_metadata("many")
        print(f"\ntest_csvpaths_metadata: meta: {meta}")
        assert meta is not None
        assert "paths_name" in meta
        assert "file_name" in meta
        assert "data_lines" in meta
        assert "csvpaths_applied" in meta
        assert "csvpaths_completed" in meta
        assert "valid" in meta
        assert meta["paths_name"] == "many"
        assert meta["file_name"] == "food"
        assert meta["data_lines"] == 11
        assert meta["csvpaths_applied"] == 2
        assert meta["csvpaths_completed"] is True
        assert meta["valid"] is True

    def test_csvpaths_metadata2(self):
        #
        # named results are cleared by CsvPaths before each run
        # the results may be identical, but they are not the same
        # data.
        #
        cs = CsvPaths()
        cs.file_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.fast_forward_by_line(filename="food", pathsname="many")
        meta = cs.results_manager.get_metadata("many")
        print(f"\ntest_csvpaths_metadata: meta: {meta}")
        assert meta is not None

        cs.collect_by_line(filename="food", pathsname="many")
        meta2 = cs.results_manager.get_metadata("many")
        assert meta2 is not None

        # cs.path_results_manager.remove_named_results("many")

        cs.collect_by_line(filename="food", pathsname="many")
        meta2 = cs.results_manager.get_metadata("many")
        assert meta2 is not None
        assert meta == meta2
        meta["x"] = 1
        assert meta != meta2

    def test_csvpaths_import_function(self):
        cs = CsvPaths()
        cs.file_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.fast_forward_by_line(filename="food", pathsname="import")
        results = cs.results_manager.get_named_results("import")
        for result in results:
            for p in result.printouts:
                print(f"\t   >> {p}")

        vs = cs.results_manager.get_variables("import")
        print(f"\n test_csvpaths_import_function: vars from import paths: {vs}")
        assert "import" in vs
        assert vs["import"] is True

    def test_csvpaths_stopping(self):
        cs = CsvPaths()
        cs.file_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        i = 0
        for line in cs.next_by_line(filename="food", pathsname="stopping"):
            print(f"test_csvpaths_stopping: lines[{i}]: {line}")
            i += 1
        cs.results_manager.get_named_results("stopping")
        vs = cs.results_manager.get_variables("stopping")
        print(f"test_csvpaths_stopping: stopping vs: {vs}")
        assert i == 7
        assert vs["one"] == [0, 1, 2]
        assert vs["two"] == [0, 1, 2, 3, 4, 5, 6]

    def test_csvpaths_correct_lines_returned1(self):
        paths = CsvPaths()
        paths.file_manager.set_named_files(FILES)
        paths.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        #
        # from 2 csvpaths we want to see:
        #   - 3 from 9 because both agree
        #   - 6 from 9 because just one agrees
        #
        lines = paths.collect_by_line(
            filename="test", pathsname="all_agree", if_all_agree=True
        )
        print(f"\n test_csvpaths_correct_lines_returned: expect 1st 3 lines: {lines}")
        assert len(lines) == 3

        lines = paths.collect_by_line(
            filename="test", pathsname="all_agree", if_all_agree=False
        )
        print(f"\n test_csvpaths_correct_lines_returned: expect first 6 lines: {lines}")
        assert len(lines) == 6

    def test_csvpaths_correct_lines_returned2(self):
        paths = CsvPaths()
        paths.file_manager.set_named_files(FILES)
        paths.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        #
        # from 2 csvpaths we want to see:
        #   - 3 of 9 returned because both agree
        #   - 6 of 9 returned because just one
        #
        lines = paths.collect_by_line(
            filename="test",
            pathsname="all_agree",
            if_all_agree=True,
            collect_when_not_matched=True,
        )
        print(
            f"\n test_csvpaths_correct_lines_returned: not matched expect last 3 lines: {lines}"
        )
        assert len(lines) == 3
        assert lines[0] == ["Ants", "Bat", "skriffle..."]
        assert lines[1] == ["Slug", "Bat", "oozeeee..."]
        assert lines[2] == ["Frog", "Bat", "growl"]

        lines = paths.collect_by_line(
            filename="test",
            pathsname="all_agree",
            if_all_agree=False,
            collect_when_not_matched=True,
        )
        print(
            f"\n test_csvpaths_correct_lines_returned: not matched expect last 6 lines: {lines}"
        )
        assert len(lines) == 6
        assert lines[0] == ["Frog", "Bat", "ribbit..."]
        assert lines[1] == ["Bug", "Bat", "sniffle sniffle..."]
        assert lines[2] == ["Bird", "Bat", "flap flap..."]
        assert lines[3] == ["Ants", "Bat", "skriffle..."]
        assert lines[4] == ["Slug", "Bat", "oozeeee..."]
        assert lines[5] == ["Frog", "Bat", "growl"]
