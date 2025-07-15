import unittest
import os
from csvpath import CsvPaths
from os import environ
from tests.csvpaths.builder import Builder

PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files{os.sep}test.csv"
NAMED_PATHS_DIR = (
    f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}"
)
SOURCE_MODE = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}source_mode.csvpaths"
FOOD = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files{os.sep}food.csv"
FOOD_PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}food.csvpaths"
FOOD_PATH_LITE = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}food_lite.csvpaths"
FILES = {
    "food": FOOD,
    "test": PATH,
}
JSON = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}sourcemode.json"


class TestCsvPathsNewCsvPaths(unittest.TestCase):
    def load(self):
        paths = Builder().build()
        paths.paths_manager.add_named_paths_from_file(
            name="sourcemode",
            file_path=SOURCE_MODE,
        )
        paths.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        paths.file_manager.set_named_files(FILES)
        paths.file_manager.add_named_file(name="sourcemode", path=PATH)
        return paths

    def test_csvpaths_next_paths_1(self):
        paths = self.load()
        paths.paths_manager.add_named_paths_from_file(
            name="food",
            file_path=FOOD_PATH,
        )
        paths.file_manager.add_named_file(
            name="food",
            path=FOOD,
        )
        cnt = 0
        for line in paths.next_paths(filename="food", pathsname="food"):
            cnt += 1
        assert cnt == 4

    def test_csvpaths_nothing(self):
        CsvPaths()

    def test_csvpaths_next_paths_2(self):
        paths = self.load()
        paths.paths_manager.add_named_paths_from_file(
            name="food", file_path=FOOD_PATH_LITE
        )
        paths.file_manager.add_named_file(name="food", path=FOOD)
        cnt = 0
        for line in paths.next_paths(filename="food", pathsname="food"):
            cnt += 1
        assert cnt == 1
        results = paths.results_manager.get_named_results("food")
        paths = None
        assert results
        assert len(results) == 1
        result = results[0]
        path = result.csvpath
        len(result) == 1
        v = path.variables
        assert v
        assert "candy" in v
        #
        # reload
        #
        paths = CsvPaths()
        results = paths.results_manager.get_named_results("food")
        assert results
        assert len(results) == 1
        result = results[0]
        path = result.csvpath
        len(result) == 1
        v = path.variables
        assert v
        assert "candy" in v

    def test_csvpaths_x_fast_forward_paths(self):
        cs = self.load()
        cs.fast_forward_paths(filename="food", pathsname="food")
        n = cs.results_manager.get_number_of_results("food")
        valid = cs.results_manager.is_valid("food")
        assert not valid
        assert n == 2
        pvars = cs.results_manager.get_variables("food")
        assert "candy" in pvars
        assert isinstance(pvars["candy"], list)
        assert pvars["candy"] == [3, 8]

    def test_csvpaths_collect_paths_1(self):
        cs = self.load()
        cs.collect_paths(filename="food", pathsname="food")
        valid = cs.results_manager.is_valid("food")
        assert not valid
        assert cs.results_manager.get_number_of_results("food") == 2
        pvars = cs.results_manager.get_variables("food")
        assert "candy" in pvars
        assert isinstance(pvars["candy"], list)
        assert pvars["candy"] == [3, 8]

    def test_csvpaths_collect_paths_2(self):
        cs = self.load()
        cs.collect_paths(filename="food", pathsname="food")
        valid = cs.results_manager.is_valid("food")
        assert not valid
        assert cs.results_manager.get_number_of_results("food") == 2
        pvars = cs.results_manager.get_variables("food")
        assert "candy" in pvars
        assert isinstance(pvars["candy"], list)
        assert pvars["candy"] == [3, 8]

    # ================= breadth first ==================

    def test_csvpaths_x_next_by_line(self):
        cs = self.load()
        cnt = 0
        for line in cs.next_by_line(filename="food", pathsname="many", collect=True):
            cnt += 1
        assert cnt == 11
        valid = cs.results_manager.is_valid("many")
        assert valid
        assert cs.results_manager.get_number_of_results("many") == 2
        pvars = cs.results_manager.get_variables("many")
        assert "one" in pvars
        assert isinstance(pvars["one"], int)
        assert pvars["one"] == 11

    def test_csvpaths_metadata1(self):
        cs = self.load()
        cs.fast_forward_by_line(filename="food", pathsname="many")
        meta = cs.results_manager.get_metadata("many")
        assert meta is not None
        assert "id" in meta
        assert "name" in meta
        assert meta["id"] == "many_two"
        assert meta["name"] == "many one"

    def test_csvpaths_metadata2(self):
        #
        # named results are cleared by CsvPaths before each run
        # the results may be identical, but they are not the same
        # data.
        #
        cs = self.load()
        cs.fast_forward_by_line(filename="food", pathsname="many")
        meta = cs.results_manager.get_metadata("many")
        assert meta is not None

        cs.collect_by_line(filename="food", pathsname="many")
        meta2 = cs.results_manager.get_metadata("many")
        assert meta2 is not None

        cs.collect_by_line(filename="food", pathsname="many")
        meta2 = cs.results_manager.get_metadata("many")
        assert meta2 is not None
        assert meta == meta2
        meta["x"] = 1
        assert meta != meta2

    def test_csvpaths_import_function(self):
        cs = self.load()
        cs.fast_forward_by_line(filename="food", pathsname="import")
        cs.results_manager.get_named_results("import")
        vs = cs.results_manager.get_variables("import")
        assert "import" in vs
        assert vs["import"] is True

    def test_csvpaths_stopping(self):
        cs = self.load()
        i = 0
        for line in cs.next_by_line(filename="food", pathsname="stopping"):
            i += 1
        cs.results_manager.get_named_results("stopping")
        vs = cs.results_manager.get_variables("stopping")
        assert i == 7
        assert vs["one"] == [0, 1, 2]
        assert vs["two"] == [0, 1, 2, 3, 4, 5, 6]

    def test_csvpaths_correct_lines_returned1(self):
        paths = self.load()
        #
        # from 2 csvpaths we want to see:
        #   - 3 from 9 because both agree
        #   - 6 from 9 because just one agrees
        #
        lines = paths.collect_by_line(
            filename="test", pathsname="all_agree", if_all_agree=True
        )
        assert len(lines) == 3
        lines = paths.collect_by_line(
            filename="test", pathsname="all_agree", if_all_agree=False
        )
        assert len(lines) == 6

    def test_csvpaths_correct_lines_returned2(self):
        paths = self.load()
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
        assert len(lines) == 6
        assert lines[0] == ["Frog", "Bat", "ribbit..."]
        assert lines[1] == ["Bug", "Bat", "sniffle sniffle..."]
        assert lines[2] == ["Bird", "Bat", "flap flap..."]
        assert lines[3] == ["Ants", "Bat", "skriffle..."]
        assert lines[4] == ["Slug", "Bat", "oozeeee..."]
        assert lines[5] == ["Frog", "Bat", "growl"]

    def test_csvpaths_source_mode(self):
        paths = self.load()
        paths.collect_paths(filename="sourcemode", pathsname="sourcemode")
        results = paths.results_manager.get_named_results("sourcemode")
        for i, r in enumerate(results):
            if i > 0:
                assert r.csvpath.data_from_preceding is True

    def test_csvpaths_replay(self):
        # os.environ["CSVPATH_CONFIG_PATH"] = "config/config.ini"
        paths = self.load()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.paths_manager.remove_named_paths("sourcemode")
        paths.file_manager.remove_named_file("sourcemode")
        paths.paths_manager.add_named_paths_from_json(file_path=JSON)
        paths.file_manager.add_named_file(name="sourcemode", path=PATH)
        #
        # do a run
        #
        paths.collect_paths(filename="sourcemode", pathsname="sourcemode")
        #
        # replay it:
        #   - filename is the last run's source1 csvpath data.csv output
        #   - path is source2:from, meaning csvpath source2 and all following paths
        #
        # the result will be another run entry in the sourcemode directory.
        # the filename and named-paths name will be visible in the metadata, along
        # with the resolved physical file path
        #
        paths = self.load()
        # paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.collect_paths(
            filename="$sourcemode.results.aprx/202:last.source1",
            pathsname="$sourcemode.csvpaths.source2:from",
        )
        results = paths.results_manager.get_named_results("sourcemode")
        for i, r in enumerate(results):
            if i > 0:
                assert r.csvpath.data_from_preceding is True
        #
        # manifests must point to the actual named_paths_name as named_results_name, not a reference
        #
        assert "named_results_name" in results[0].run_manifest
        assert results[0].run_manifest["named_results_name"] == "sourcemode"
        #
        #
        #
        assert "named_results_name" in results[0].manifest
        assert results[0].manifest["named_results_name"] == "sourcemode"
