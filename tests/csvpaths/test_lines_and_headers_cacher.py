import unittest
import os
import shutil
from csvpath import CsvPaths
from csvpath.util.line_monitor import LineMonitor
from csvpath.util.path_util import PathUtility as pathu
from csvpath.util.nos import Nos
from csvpath.util.cache import Cache
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.file_readers import DataFileReader

from csvpath.util.line_counter import LineCounter

from tests.csvpaths.builder import Builder

PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}test.csv"
FILES = {
    "food": f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files{os.sep}food.csv",
    "test": f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files{os.sep}test.csv",
}
NAMED_PATHS_DIR = (
    f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}"
)


class TestCsvPathsLinesAndHeadersCacher(unittest.TestCase):
    def test_csvpaths_lines_and_headers_cacher_0(self) -> None:
        paths = Builder().build()
        paths.config.add_to_config("cache", "use_cache", "yes")
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        cachedir = paths.file_manager.lines_and_headers_cacher.cache.get_cachedir()
        nos = Nos(cachedir)
        if nos.backend != "local":
            print("caching is currently only supported in local files")
            return
        assert paths.config.get(section="cache", name="path") == "cache" == cachedir
        _ = paths.config.get(section="cache", name="use_cache")
        assert isinstance(_, str)
        _ = _.strip().lower()
        assert _ in ["true", "on", "yes"]

    def test_csvpaths_lines_and_headers_cacher_1(self):
        paths = Builder().build()
        paths.config.add_to_config("cache", "use_cache", "yes")
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        cachedir = paths.file_manager.lines_and_headers_cacher.cache.get_cachedir()
        nos = Nos(cachedir)
        if nos.backend != "local":
            print("caching is currently only supported in local files")
            return
        print(f"cache dir: {cachedir} -> {os.getcwd()}")
        shutil.rmtree(cachedir)
        assert not os.path.exists(cachedir)

        paths.file_manager.add_named_file(name="food", path=FILES["food"])
        paths.file_manager.add_named_file(name="test", path=FILES["test"])
        paths.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        #
        # cache populates when named-files are used
        #
        paths.fast_forward_paths(filename="food", pathsname="advancing")
        assert len(Nos(cachedir).listdir()) == 1
        paths.fast_forward_paths(filename="food", pathsname="advancing")
        assert len(Nos(cachedir).listdir()) == 1
        paths.fast_forward_paths(filename="test", pathsname="advancing")
        assert len(Nos(cachedir).listdir()) == 2

    def test_csvpaths_lines_and_headers_cacher_2(self):
        paths = Builder().build()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.config.add_to_config("cache", "use_cache", "yes")
        paths.config.add_to_config("cache", "path", "cache")
        cachedir = paths.file_manager.lines_and_headers_cacher.cache.get_cachedir()
        assert cachedir
        assert cachedir == "cache"
        assert os.path.exists(cachedir)
        shutil.rmtree(cachedir)
        assert not os.path.exists(cachedir)
        paths = Builder().build()
        paths.config.add_to_config("cache", "use_cache", "yes")
        paths.config.add_to_config("cache", "path", "cache")
        cachedir = paths.file_manager.lines_and_headers_cacher.cache.get_cachedir()
        assert os.path.exists(cachedir)

    def test_csvpaths_lines_and_headers_cacher_4(self):
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
        cache.cache_text(filename, jstr)
        # same cache object
        jstr2 = cache.cached_text(filename)
        assert jstr == jstr2
        lm2 = LineMonitor()
        lm2.load(jstr2)
        assert lm.physical_end_line_count == lm2.physical_end_line_count
        assert lm.physical_end_line_number == lm2.physical_end_line_number
        assert lm.data_end_line_count == lm2.data_end_line_count
        assert lm.data_end_line_number == lm2.data_end_line_number
        paths.config.add_to_config("cache", "use_cache", v)

    def test_csvpaths_lines_and_headers_cacher_5(self):
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
        cache.cache_text(filename, jstr)
        # new csvpaths, new cache object
        paths = Builder().build()
        paths.config.add_to_config("cache", "use_cache", "yes")
        paths.config.add_to_config("cache", "path", "cache")
        cache = paths.file_manager.lines_and_headers_cacher.cache
        jstr2 = cache.cached_text(filename)
        assert jstr == jstr2
        lm2 = LineMonitor()
        lm2.load(jstr2)
        assert lm.physical_end_line_count == lm2.physical_end_line_count
        assert lm.physical_end_line_number == lm2.physical_end_line_number
        assert lm.data_end_line_count == lm2.data_end_line_count
        assert lm.data_end_line_number == lm2.data_end_line_number
        paths.config.add_to_config("cache", "use_cache", v)
