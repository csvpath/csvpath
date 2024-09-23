import unittest
import os
import shutil
from csvpath import CsvPaths
from csvpath.util.line_monitor import LineMonitor

PATH = "tests/test_resources/test.csv"
FILES = {
    "food": "tests/test_resources/named_files/food.csv",
    "test": "tests/test_resources/named_files/test.csv",
}
NAMED_PATHS_DIR = "tests/test_resources/named_paths/"


class TestCache(unittest.TestCase):
    def test_cache_files(self):
        cs = CsvPaths()
        cachedir = cs.file_manager.cache._cachedir()
        shutil.rmtree(cachedir)
        assert not os.path.exists(cachedir)
        cs.file_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.fast_forward_paths(filename="food", pathsname="advancing")
        assert len(cs.file_manager.pathed_lines_and_headers) == 1
        assert cachedir
        assert os.path.exists(cachedir)
        assert len(os.listdir(cachedir)) == 2

    def test_cache_dir(self):
        csvpaths = CsvPaths()
        cachedir = csvpaths.file_manager.cache._cachedir()
        assert cachedir
        assert os.path.exists(cachedir)
        shutil.rmtree(cachedir)
        assert not os.path.exists(cachedir)
        csvpaths = CsvPaths()
        cachedir = csvpaths.file_manager.cache._cachedir()
        assert os.path.exists(cachedir)

    def test_cache_csv(self):
        csvpaths = CsvPaths()
        cache = csvpaths.file_manager.cache
        filename = "/a/file/name"
        headers = ["a", "header", "row"]
        cache.cache_text(filename, "csv", ",".join(headers))
        csvpaths = CsvPaths()
        cache = csvpaths.file_manager.cache
        cheaders = cache.cached_text(filename, "csv")
        assert cheaders == headers
        assert len(cheaders) == len(headers)

    def test_cache_line_mon1(self):
        csvpaths = CsvPaths()
        cache = csvpaths.file_manager.cache
        filename = PATH
        lm = LineMonitor()
        lm._physical_end_line_count = 10
        lm._physical_end_line_number = 20
        lm._data_end_line_count = 15
        lm._data_end_line_number = 25
        jstr = lm.dump()
        cache.cache_text(filename, "json", jstr)
        # same cache object
        jstr2 = cache.cached_text(filename, "json")
        assert jstr == jstr2
        lm2 = LineMonitor()
        lm2.load(jstr2)
        assert lm.physical_end_line_count == lm2.physical_end_line_count
        assert lm.physical_end_line_number == lm2.physical_end_line_number
        assert lm.data_end_line_count == lm2.data_end_line_count
        assert lm.data_end_line_number == lm2.data_end_line_number

    def test_cache_line_mon2(self):
        csvpaths = CsvPaths()
        cache = csvpaths.file_manager.cache
        filename = PATH
        lm = LineMonitor()
        lm._physical_end_line_count = 10
        lm._physical_end_line_number = 20
        lm._data_end_line_count = 15
        lm._data_end_line_number = 25
        jstr = lm.dump()
        cache.cache_text(filename, "json", jstr)
        # new csvpaths, new cache object
        csvpaths = CsvPaths()
        cache = csvpaths.file_manager.cache
        jstr2 = cache.cached_text(filename, "json")
        assert jstr == jstr2
        lm2 = LineMonitor()
        lm2.load(jstr2)
        assert lm.physical_end_line_count == lm2.physical_end_line_count
        assert lm.physical_end_line_number == lm2.physical_end_line_number
        assert lm.data_end_line_count == lm2.data_end_line_count
        assert lm.data_end_line_number == lm2.data_end_line_number
