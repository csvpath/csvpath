import unittest
import os
import shutil
from csvpath import CsvPaths
from csvpath.util.line_monitor import LineMonitor
from csvpath.util.path_util import PathUtility as pathu
from csvpath.util.nos import Nos
from csvpath.util.file_writers import DataFileWriter
from tests.csvpaths.builder import Builder

PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}test.csv"
FILES = {
    "food": f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files{os.sep}food.csv",
    "test": f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files{os.sep}test.csv",
}
NAMED_PATHS_DIR = (
    f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}"
)


class TestCsvPathsCache(unittest.TestCase):
    def test_cache_files(self):
        paths = Builder().build()
        v = paths.config.get(section="cache", name="use_cache")
        paths.config.add_to_config("cache", "path", "cache")
        paths.config.add_to_config("cache", "use_cache", "yes")
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        cachedir = paths.file_manager.lines_and_headers_cacher.cache._cachedir()
        shutil.rmtree(cachedir)
        assert not os.path.exists(cachedir)
        paths.file_manager.set_named_files(FILES)
        paths.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        paths.fast_forward_paths(filename="food", pathsname="advancing")
        assert (
            len(paths.file_manager.lines_and_headers_cacher.pathed_lines_and_headers)
            == 1
        )
        assert cachedir
        assert os.path.exists(cachedir)
        assert len(os.listdir(cachedir)) == 2
        paths.config.add_to_config("cache", "use_cache", v)

    def test_cache_dir(self):
        paths = Builder().build()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.config.add_to_config("cache", "use_cache", "yes")
        paths.config.add_to_config("cache", "path", "cache")
        cachedir = paths.file_manager.lines_and_headers_cacher.cache._cachedir()
        assert cachedir
        assert cachedir == "cache"
        assert os.path.exists(cachedir)
        shutil.rmtree(cachedir)
        assert not os.path.exists(cachedir)
        paths = Builder().build()
        paths.config.add_to_config("cache", "use_cache", "yes")
        paths.config.add_to_config("cache", "path", "cache")
        cachedir = paths.file_manager.lines_and_headers_cacher.cache._cachedir()
        assert os.path.exists(cachedir)

    def test_cache_csv(self):
        paths = Builder().build()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        v = paths.config.get(section="cache", name="use_cache")
        paths.config.add_to_config("cache", "use_cache", "yes")
        paths.config.add_to_config("cache", "path", "cache")
        cache = paths.file_manager.lines_and_headers_cacher.cache
        filename = os.path.join("tests", "csvpath", "test_resources", "deleteme.csv")
        nos = Nos(filename)
        headers = ["a", "header", "row"]
        txt = ",".join(headers)
        if nos.exists():
            nos.remove()
        with DataFileWriter(path=filename) as file:
            file.write(txt)
        cache.cache_text(filename, "csv", txt)
        paths = Builder().build()
        paths.config.add_to_config("cache", "use_cache", "yes")
        paths.config.add_to_config("cache", "path", "cache")
        cache = paths.file_manager.lines_and_headers_cacher.cache
        filename = pathu.resep(filename)
        cheaders = cache.cached_text(filename, "csv")
        assert cheaders == headers
        assert len(cheaders) == len(headers)
        paths.config.add_to_config("cache", "use_cache", v)
        nos.remove()

    def test_cache_line_mon1(self):
        paths = Builder().build()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        v = paths.config.get(section="cache", name="use_cache")
        paths.config.add_to_config("cache", "use_cache", "yes")
        paths.config.add_to_config("cache", "path", "cache")
        cache = paths.file_manager.lines_and_headers_cacher.cache
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
        paths.config.add_to_config("cache", "use_cache", v)

    def test_cache_line_mon2(self):
        paths = Builder().build()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        v = paths.config.get(section="cache", name="use_cache")
        paths.config.add_to_config("cache", "use_cache", "yes")
        paths.config.add_to_config("cache", "path", "cache")
        cache = paths.file_manager.lines_and_headers_cacher.cache
        filename = PATH
        lm = LineMonitor()
        lm._physical_end_line_count = 10
        lm._physical_end_line_number = 20
        lm._data_end_line_count = 15
        lm._data_end_line_number = 25
        jstr = lm.dump()
        cache.cache_text(filename, "json", jstr)
        # new csvpaths, new cache object
        paths = Builder().build()
        paths.config.add_to_config("cache", "use_cache", "yes")
        paths.config.add_to_config("cache", "path", "cache")
        cache = paths.file_manager.lines_and_headers_cacher.cache
        jstr2 = cache.cached_text(filename, "json")
        assert jstr == jstr2
        lm2 = LineMonitor()
        lm2.load(jstr2)
        assert lm.physical_end_line_count == lm2.physical_end_line_count
        assert lm.physical_end_line_number == lm2.physical_end_line_number
        assert lm.data_end_line_count == lm2.data_end_line_count
        assert lm.data_end_line_number == lm2.data_end_line_number
        paths.config.add_to_config("cache", "use_cache", v)
