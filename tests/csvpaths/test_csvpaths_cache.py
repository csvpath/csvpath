import unittest
import os
from csvpath.util.nos import Nos
from csvpath.util.cache import Cache
from tests.csvpaths.builder import Builder

PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathsCache(unittest.TestCase):
    def test_csvpaths_cache_name(self) -> None:
        paths = Builder().build()
        cache = Cache(paths)
        name1 = cache.get_cache_name(PATH)
        name2 = cache.get_cache_name(PATH)
        name1 == name2

    def test_csvpaths_cache_dir(self) -> None:
        paths = Builder().build()
        cache = Cache(paths)
        path = cache.get_cachedir()
        assert path
        assert paths.config.cache_dir_path == path
        assert paths.config.get(section="cache", name="path")
        assert os.path.exists(path)

    def test_csvpaths_cache_keypath(self) -> None:
        paths = Builder().build()
        cache = Cache(paths)
        keypath1 = cache.get_keypath(PATH)
        keypath2 = cache.get_keypath(PATH)
        assert keypath1
        assert keypath1 == keypath2

    def test_csvpaths_cache_text(self) -> None:
        paths = Builder().build()
        cache = Cache(paths)
        cache.clear_cache()
        js1 = {"headers": ["a", "b", "c"]}
        cache.cache_text(PATH, js1)
        js2 = cache.cached_text(PATH)
        assert js2
        assert js1 == js2
        js3 = {"headers": ["d", "e", "f"]}
        cache.cache_text(PATH, js3)
        js4 = cache.cached_text(PATH)
        assert js4
        assert js4 == js3
        assert js3 != js2
        cachedir = cache.get_cachedir()
        assert len(Nos(cachedir).listdir()) == 1
