import unittest
import os
import shutil
from csvpath import CsvPaths
from csvpath.util.line_monitor import LineMonitor
from csvpath.util.path_util import PathUtility as pathu

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"
FILES = {
    "food": f"tests{os.sep}test_resources{os.sep}named_files{os.sep}food.csv",
    "test": f"tests{os.sep}test_resources{os.sep}named_files{os.sep}test.csv",
}
NAMED_PATHS_DIR = f"tests{os.sep}test_resources{os.sep}named_paths{os.sep}"


class TestCache(unittest.TestCase):
    def test_cache_files(self):
        cs = CsvPaths()
        v = cs.config.get(section="cache", name="use_cache")
        cs.config.add_to_config("cache", "use_cache", "yes")
        cs.add_to_config("errors", "csvpath", "raise, collect, print")
        cachedir = cs.file_manager.lines_and_headers_cacher.cache._cachedir()
        shutil.rmtree(cachedir)
        assert not os.path.exists(cachedir)
        cs.file_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.fast_forward_paths(filename="food", pathsname="advancing")
        assert (
            len(cs.file_manager.lines_and_headers_cacher.pathed_lines_and_headers) == 1
        )
        assert cachedir
        assert os.path.exists(cachedir)
        assert len(os.listdir(cachedir)) == 2
        cs.config.add_to_config("cache", "use_cache", v)

    def test_cache_dir(self):
        csvpaths = CsvPaths()
        csvpaths.add_to_config("errors", "csvpath", "raise, collect, print")
        v = csvpaths.config.get(section="cache", name="use_cache")
        csvpaths.config.add_to_config("cache", "use_cache", "yes")
        cachedir = csvpaths.file_manager.lines_and_headers_cacher.cache._cachedir()
        assert cachedir
        assert os.path.exists(cachedir)
        shutil.rmtree(cachedir)
        assert not os.path.exists(cachedir)
        csvpaths = CsvPaths()
        csvpaths.config.add_to_config("cache", "use_cache", "yes")
        cachedir = csvpaths.file_manager.lines_and_headers_cacher.cache._cachedir()
        assert os.path.exists(cachedir)
        csvpaths.config.add_to_config("cache", "use_cache", v)

    def test_cache_csv(self):
        csvpaths = CsvPaths()
        csvpaths.add_to_config("errors", "csvpath", "raise, collect, print")
        v = csvpaths.config.get(section="cache", name="use_cache")
        csvpaths.config.add_to_config("cache", "use_cache", "yes")
        cache = csvpaths.file_manager.lines_and_headers_cacher.cache
        filename = "/a/file/name"
        headers = ["a", "header", "row"]
        cache.cache_text(filename, "csv", ",".join(headers))
        csvpaths = CsvPaths()
        cache = csvpaths.file_manager.lines_and_headers_cacher.cache
        filename = pathu.resep(filename)
        cheaders = cache.cached_text(filename, "csv")
        assert cheaders == headers
        assert len(cheaders) == len(headers)
        csvpaths.config.add_to_config("cache", "use_cache", v)

    def test_cache_line_mon1(self):
        csvpaths = CsvPaths()
        csvpaths.add_to_config("errors", "csvpath", "raise, collect, print")
        v = csvpaths.config.get(section="cache", name="use_cache")
        csvpaths.config.add_to_config("cache", "use_cache", "yes")
        cache = csvpaths.file_manager.lines_and_headers_cacher.cache
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
        csvpaths.config.add_to_config("cache", "use_cache", v)

    def test_cache_line_mon2(self):
        csvpaths = CsvPaths()
        csvpaths.add_to_config("errors", "csvpath", "raise, collect, print")
        v = csvpaths.config.get(section="cache", name="use_cache")
        csvpaths.config.add_to_config("cache", "use_cache", "yes")
        cache = csvpaths.file_manager.lines_and_headers_cacher.cache
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
        cache = csvpaths.file_manager.lines_and_headers_cacher.cache
        jstr2 = cache.cached_text(filename, "json")
        assert jstr == jstr2
        lm2 = LineMonitor()
        lm2.load(jstr2)
        assert lm.physical_end_line_count == lm2.physical_end_line_count
        assert lm.physical_end_line_number == lm2.physical_end_line_number
        assert lm.data_end_line_count == lm2.data_end_line_count
        assert lm.data_end_line_number == lm2.data_end_line_number
        csvpaths.config.add_to_config("cache", "use_cache", v)
