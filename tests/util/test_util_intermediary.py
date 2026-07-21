import json
import os
import unittest
from csvpath.util.intermediary import (
    Intermediary,
    CacheIntermediary,
    NoCacheIntermediary,
)
from csvpath.util.config import Config
from csvpath.util.nos import Nos

TMP_DIR = os.path.join("tests", "util", "test_resources", "tmp", "intermediary")


class FakeCsvPaths:
    def __init__(self, use_cache: str = "yes"):
        self.config = Config()
        self.config.set(section="cache", name="use_cache", value=use_cache)


class TestUtilIntermediary(unittest.TestCase):
    def setUp(self):
        nos = Nos(TMP_DIR)
        if not nos.dir_exists():
            nos.makedirs()
        Intermediary.HIT_COUNT = 0
        Intermediary.MISS_COUNT = 0
        Intermediary.WRITE_COUNT = 0

    def tearDown(self):
        nos = Nos(TMP_DIR)
        if nos.dir_exists():
            nos.remove()

    def _path(self, name: str) -> str:
        return os.path.join(TMP_DIR, name)

    #
    # factory (__new__)
    #
    def test_factory_returns_cache_intermediary_by_default(self):
        i = Intermediary(FakeCsvPaths(use_cache="yes"))
        assert isinstance(i, CacheIntermediary)

    def test_factory_returns_no_cache_intermediary_when_use_cache_no(self):
        i = Intermediary(FakeCsvPaths(use_cache="no"))
        assert isinstance(i, NoCacheIntermediary)

    def test_factory_is_case_insensitive_for_no(self):
        i = Intermediary(FakeCsvPaths(use_cache="No"))
        assert isinstance(i, NoCacheIntermediary)

    #
    # CacheIntermediary
    #
    def test_cache_get_json_missing_file_returns_empty_and_persists_it(self):
        path = self._path("missing.json")
        i = CacheIntermediary(FakeCsvPaths())
        result = i.get_json(path)
        assert result == []
        assert Nos(path).exists()
        with open(path, "r", encoding="utf-8") as f:
            assert json.load(f) == []

    def test_cache_get_json_second_call_is_a_cache_hit_not_a_reread(self):
        path = self._path("hitcheck.json")
        i = CacheIntermediary(FakeCsvPaths())
        i.put_json(path, {"a": 1})
        first = i.get_json(path)
        # change the file on disk directly -- if the second get_json() were
        # reading from disk instead of the in-memory cache, it would see this
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"a": 999}, f)
        second = i.get_json(path)
        assert first == {"a": 1}
        assert second == {"a": 1}

    def test_cache_counts_hits_and_misses(self):
        path = self._path("counts.json")
        i = CacheIntermediary(FakeCsvPaths())
        i.get_json(path)  # miss (file does not exist yet)
        i.get_json(path)  # hit
        i.get_json(path)  # hit
        assert Intermediary.MISS_COUNT == 1
        assert Intermediary.HIT_COUNT == 2

    def test_cache_put_json_writes_through_and_updates_cache(self):
        path = self._path("put.json")
        i = CacheIntermediary(FakeCsvPaths())
        i.put_json(path, {"b": 2})
        with open(path, "r", encoding="utf-8") as f:
            assert json.load(f) == {"b": 2}
        # served from cache without touching disk again
        assert i.get_json(path) == {"b": 2}

    def test_cache_clear_forces_a_reread_from_disk(self):
        path = self._path("clear.json")
        i = CacheIntermediary(FakeCsvPaths())
        i.put_json(path, {"c": 3})
        i.clear(path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"c": 999}, f)
        assert i.get_json(path) == {"c": 999}

    #
    # NoCacheIntermediary
    #
    def test_no_cache_get_json_missing_file_returns_empty_without_writing(self):
        path = self._path("nocache_missing.json")
        i = NoCacheIntermediary(FakeCsvPaths(use_cache="no"))
        result = i.get_json(path)
        assert result == []
        # unlike CacheIntermediary, a miss does not create the file
        assert not Nos(path).exists()

    def test_no_cache_put_and_get_roundtrip(self):
        path = self._path("nocache_roundtrip.json")
        i = NoCacheIntermediary(FakeCsvPaths(use_cache="no"))
        i.put_json(path, {"d": 4})
        assert i.get_json(path) == {"d": 4}

    def test_no_cache_reads_live_from_disk_every_time(self):
        path = self._path("nocache_live.json")
        i = NoCacheIntermediary(FakeCsvPaths(use_cache="no"))
        i.put_json(path, {"e": 5})
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"e": 999}, f)
        assert i.get_json(path) == {"e": 999}

    def test_no_cache_clear_is_a_noop(self):
        i = NoCacheIntermediary(FakeCsvPaths(use_cache="no"))
        i.clear("does-not-matter")  # must not raise
