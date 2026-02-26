import unittest
import os
from csvpath import CsvPaths
from csvpath.util.line_spooler import LineSpooler
from csvpath.managers.results.readers.readers import ResultReadersFacade
from csvpath.managers.results.result_file_reader import ResultFileReader
from csvpath.util.file_readers import FileInfo
from csvpath.util.line_spooler import CsvLineSpooler
from csvpath.util.path_util import PathUtility as pathu
from csvpath.util.nos import Nos
from tests.csvpaths.builder import Builder
from tests.csvpaths.kit.tracking_file_manager import TrackingFileManager
from tests.csvpaths.kit.tracking_paths_manager import TrackingPathsManager


def setup_module(module):
    ...


DELETEME = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}deleteme"
FOOD = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}food.csvpaths"
FOOD_CSV = (
    f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files{os.sep}food.csv"
)
PEOPLE = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}people.csvpaths"
PEOPLE_CSV = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}test.csv"
ERROR = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}error_reload.csvpath"


class TestCsvPathsManagersResultReaders(unittest.TestCase):
    def _setup(self) -> None:
        paths = Builder().build()
        paths.paths_manager.add_named_paths(name="food", from_file=FOOD)
        paths.paths_manager.add_named_paths(name="arrivals", from_file=PEOPLE)
        paths.paths_manager.add_named_paths(name="error_reload", from_file=ERROR)
        paths.file_manager.add_named_file(name="food", path=FOOD_CSV)
        paths.file_manager.add_named_file(name="people", path=PEOPLE_CSV)
        return paths

    def test_result_readers(self):
        f = ResultReadersFacade(None)
        f.load_readers()
        assert f.errors_reader
        assert f.unmatched_reader
        assert f.printouts_reader
        assert f.lines_reader

    def test_reload_result_spooler_instance_data_file_path(self):
        paths = self._setup()
        paths.collect_paths(pathsname="food", filename="food")
        results = paths.results_manager.get_named_results("food")
        result = results[0]
        cs = CsvLineSpooler(None)
        dpath = cs._instance_data_file_path()
        assert dpath is None
        cs = CsvLineSpooler(result)
        c = result.csvpath
        result.csvpath = None
        dpath = cs._instance_data_file_path()
        assert dpath is None
        result.csvpath = c
        dpath = result.data_file_path
        assert dpath is not None
        assert pathu.equal(dpath, cs.path)
        dpath = result.data_file_path
        assert dpath is not None
        assert pathu.equal(dpath, cs.path)

    def test_reload_result_reader_helpers(self):
        paths = self._setup()
        paths.collect_paths(pathsname="food", filename="food")
        #
        # paths does clean() and set_managers() so we would need to renew our wrapped
        # versions. however, we don't need to tear down and shouldn't
        #
        # paths.file_manager = TrackingFileManager(csvpaths=paths, mgr=paths.file_manager)
        # paths.paths_manager = TrackingPathsManager(csvpaths=paths, mgr=paths.paths_manager)
        results = paths.results_manager.get_named_results("food")
        result = results[0]
        result_dir = Nos(result.run_dir).join(result.identity_or_index)
        # result_dir = os.path.join(result.run_dir, result.identity_or_index)
        m = ResultFileReader.meta(result_dir)
        assert m is not None
        assert len(m) > 0
        assert "runtime_data" in m
        assert m["runtime_data"]["delimiter"] == ","

        print(f"result_dir: {result_dir}")
        m = ResultFileReader.manifest(result_dir)
        assert m is not None
        assert len(m) > 0
        assert "instance_home" in m
        assert m["instance_home"] == result_dir

        if paths.config.archive_path.find("://") > -1:
            print("Not checking file info because atm we don't support file info in S3")
        else:
            info = FileInfo.info(m["manifest_path"])
            assert info
            assert "created" in info
            assert info["created"] is not None

    def test_reload_result_file_lines_reader(self):
        paths = self._setup()
        paths.collect_paths(pathsname="food", filename="food")
        #
        # paths does clean() and set_managers() so we need to renew our wrapped versions
        #
        paths.file_manager = TrackingFileManager(csvpaths=paths, mgr=paths.file_manager)
        paths.paths_manager = TrackingPathsManager(
            csvpaths=paths, mgr=paths.paths_manager
        )
        results = paths.results_manager.get_named_results("food")
        assert len(results) == 2
        result = results[0]
        lines = result.lines
        assert lines
        assert isinstance(lines, LineSpooler)
        #
        # now ready to reload
        #
        readers = ResultReadersFacade(result)
        lines2 = readers.lines
        assert lines2 is not None
        assert len(lines2) == 1
        assert len(lines) == len(lines2)

    def test_reload_errors(self):
        paths = self._setup()
        paths.collect_paths(pathsname="error_reload", filename="people")
        results = paths.results_manager.get_named_results("error_reload")
        assert results is not None
        assert len(results) == 1
        errors = results[0].errors
        assert errors
        assert len(errors) == 8
        #
        # reload
        #
        paths = Builder().build()
        results = paths.results_manager.get_named_results("error_reload")
        assert results is not None
        assert len(results) == 1

        errors2 = results[0].errors
        assert errors2 is not None
        assert len(errors2) == len(errors)
        errors[0].how_eq(errors2[0])
        assert errors[0] == errors2[0]

    def test_reload_printouts(self):
        paths = self._setup()
        paths.collect_paths(pathsname="arrivals", filename="people")
        results = paths.results_manager.get_named_results("arrivals")
        assert results is not None
        assert len(results) == 2
        printouts = results[0].get_printouts("name_tags")
        assert printouts
        assert len(printouts) == 7
        assert results[0].has_printouts()
        printouts = results[0].get_printouts("checklist")
        assert printouts
        assert len(printouts) == 8
        #
        #
        #
        paths = Builder().build()
        results2 = paths.results_manager.get_named_results("arrivals")
        assert results2 is not None
        assert len(results2) == 2
        printouts = results2[0].get_printouts("name_tags")
        assert printouts
        assert len(printouts) == 7
        printouts = results2[1].get_printouts("remarks")
        assert printouts
        assert len(printouts) == 3

    def test_reload_lines(self):
        paths = self._setup()
        paths.collect_paths(pathsname="arrivals", filename="people")
        results = paths.results_manager.get_named_results("arrivals")
        assert results is not None
        assert len(results) == 2
        assert len(results[0]) == 8
        #
        #
        #
        paths = Builder().build()
        results2 = paths.results_manager.get_named_results("arrivals")
        assert results2 is not None
        assert len(results2) == 2
        assert len(results2[0]) == 8

        lst1 = results[0].lines.to_list()
        lst2 = results2[0].lines.to_list()
        assert len(lst1) == len(lst2)
        for i, _ in enumerate(lst1):
            assert lst1[i] == lst2[i]

        assert results2[0].is_valid

    def test_reload_unmatched(self):
        paths = self._setup()
        paths.collect_paths(pathsname="arrivals", filename="people")
        results = paths.results_manager.get_named_results("arrivals")
        assert results is not None
        assert len(results) == 2
        #
        #
        #
        paths = Builder().build()
        results2 = paths.results_manager.get_named_results("arrivals")
        assert results2 is not None
        assert len(results2) == 2

        lst1 = results[0].unmatched
        lst2 = results2[0].unmatched.to_list()
        assert len(lst1) == 1
        assert len(lst1) == len(lst2)
        for i, _ in enumerate(lst1):
            assert lst1[i] == lst2[i]

        lst1 = results[1].unmatched
        lst2 = results2[1].unmatched.to_list()
        assert len(lst1) == 6
        assert len(lst1) == len(lst2)
        for i, _ in enumerate(lst1):
            assert lst1[i] == lst2[i]

    def test_reload_result_reader_helpers_2(self):
        p = DELETEME
        if not os.path.exists(p):
            os.makedirs(p)
        f = os.path.join(p, "meta.json")
        if os.path.exists(f):
            os.remove(f)
        m = ResultFileReader.meta(p)
        assert m is not None
        assert len(m) == 0
        assert os.path.exists(f)
        os.remove(f)
        assert not os.path.exists(f)
        #
        #
        #
        f = os.path.join(p, "manifest.json")
        m = ResultFileReader.manifest(p)
        assert m is not None
        assert len(m) == 0
        assert os.path.exists(f)
        os.remove(f)
        assert not os.path.exists(f)
