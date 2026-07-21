import os
import unittest
import pytest
import pylightxl as xl
from csvpath import CsvPath
from csvpath.util.cache import Cache
from csvpath.util.nos import Nos
from csvpath.managers.files.lines_and_headers_cacher import LinesAndHeadersCacher

TEST_FILE = os.path.join("tests", "util", "test_resources", "test.csv")
CACHE_DIR = os.path.join("tests", "util", "test_resources", "tmp", "cache")
TWO_SHEET_XLSX = os.path.join(
    "tests", "util", "test_resources", "tmp", "two_sheets.xlsx"
)


class TestUtilCache(unittest.TestCase):
    def setUp(self):
        nos = Nos(CACHE_DIR)
        if nos.dir_exists():
            nos.remove()

    def tearDown(self):
        nos = Nos(CACHE_DIR)
        if nos.dir_exists():
            nos.remove()

    def _cache(self) -> Cache:
        path = CsvPath()
        path.config.cache_dir_path = CACHE_DIR
        return Cache(path)

    #
    # get_cache_name()
    #
    def test_get_cache_name_none_raises(self):
        cache = self._cache()
        with pytest.raises(ValueError):
            cache.get_cache_name(None)

    def test_get_cache_name_is_stable_for_same_file(self):
        cache = self._cache()
        name1 = cache.get_cache_name(TEST_FILE)
        name2 = cache.get_cache_name(TEST_FILE)
        assert name1 is not None
        assert name1 == name2

    def test_get_cache_name_missing_file_returns_none(self):
        cache = self._cache()
        name = cache.get_cache_name(
            os.path.join("tests", "util", "test_resources", "does_not_exist.csv")
        )
        assert name is None

    def test_get_cache_name_directory_does_not_raise(self):
        # os.path.getmtime() succeeds on directories too, so the
        # IsADirectoryError guard in get_cache_name() is not actually hit
        # here -- a directory hashes just like a file would.
        cache = self._cache()
        name = cache.get_cache_name(os.path.join("tests", "util", "test_resources"))
        assert name is not None

    #
    # get_cachedir()
    #
    def test_get_cachedir_matches_config_and_exists(self):
        cache = self._cache()
        cachedir = cache.get_cachedir()
        assert cachedir == CACHE_DIR
        assert os.path.exists(cachedir)

    #
    # get_keypath()
    #
    def test_get_keypath_none_raises(self):
        cache = self._cache()
        with pytest.raises(ValueError):
            cache.get_keypath(None)

    def test_get_keypath_is_stable_and_json(self):
        cache = self._cache()
        keypath1 = cache.get_keypath(TEST_FILE)
        keypath2 = cache.get_keypath(TEST_FILE)
        assert keypath1 == keypath2
        assert keypath1.endswith(".json")
        assert keypath1.startswith(CACHE_DIR)

    def test_get_keypath_distinguishes_root_minor_tokens(self):
        # regression test for a real bug: get_keypath() used to strip the
        # root-minor (worksheet tab) token before hashing, so every tab of
        # the same Excel file collapsed onto the same cache key.
        # LinesAndHeadersCacher caches headers/line counts per filename
        # including the tab, so that collision meant every worksheet after
        # the first-accessed one silently got served the first worksheet's
        # cached headers and line count. See
        # test_lines_and_headers_cacher_does_not_collide_across_sheets below
        # for the end-to-end reproduction that caught this.
        cache = self._cache()
        keypath_plain = cache.get_keypath(TEST_FILE)
        keypath_sheet1 = cache.get_keypath(f"{TEST_FILE}#Sheet1")
        keypath_sheet2 = cache.get_keypath(f"{TEST_FILE}#Sheet2")
        assert keypath_plain != keypath_sheet1
        assert keypath_sheet1 != keypath_sheet2

    def test_get_keypath_same_root_minor_token_is_stable(self):
        cache = self._cache()
        keypath1 = cache.get_keypath(f"{TEST_FILE}#Sheet1")
        keypath2 = cache.get_keypath(f"{TEST_FILE}#Sheet1")
        assert keypath1 == keypath2

    def test_get_cache_name_uses_real_path_mtime_with_root_minor_token(self):
        # the mtime lookup inside get_cache_name() must use the real path
        # (without the #tab suffix) or it would always fail with a
        # FileNotFoundError for any Excel-tab-qualified filename
        cache = self._cache()
        name = cache.get_cache_name(f"{TEST_FILE}#Sheet1")
        assert name is not None

    def test_get_keypath_missing_file_returns_none(self):
        cache = self._cache()
        keypath = cache.get_keypath(
            os.path.join("tests", "util", "test_resources", "does_not_exist.csv")
        )
        assert keypath is None

    #
    # cache_text() / cached_text()
    #
    def test_cache_and_cached_text_roundtrip(self):
        cache = self._cache()
        data = {"headers": ["a", "b", "c"]}
        cache.cache_text(TEST_FILE, data)
        got = cache.cached_text(TEST_FILE)
        assert got == data

    def test_cache_text_overwrites_previous_value(self):
        cache = self._cache()
        cache.cache_text(TEST_FILE, {"headers": ["a", "b"]})
        cache.cache_text(TEST_FILE, {"headers": ["c", "d"]})
        got = cache.cached_text(TEST_FILE)
        assert got == {"headers": ["c", "d"]}

    def test_cached_text_before_any_cache_write_returns_none(self):
        cache = self._cache()
        assert cache.cached_text(TEST_FILE) is None

    def test_cache_text_missing_file_raises(self):
        # get_keypath() returns None for a file that does not exist, and
        # cache_text() turns that into a ValueError rather than silently
        # writing nowhere.
        cache = self._cache()
        with pytest.raises(ValueError):
            cache.cache_text(
                os.path.join("tests", "util", "test_resources", "does_not_exist.csv"),
                {"a": 1},
            )

    #
    # clear_cache()
    #
    def test_clear_cache_removes_cached_entries(self):
        cache = self._cache()
        cache.cache_text(TEST_FILE, {"headers": ["a", "b"]})
        assert cache.cached_text(TEST_FILE) is not None
        cache.clear_cache()
        assert not Nos(CACHE_DIR).dir_exists()

    #
    # end-to-end regression for the root-minor cache collision bug
    #
    def test_lines_and_headers_cacher_does_not_collide_across_sheets(self):
        db = xl.Database()
        db.add_ws(ws="SheetA")
        db.ws(ws="SheetA").update_index(row=1, col=1, val="alpha_header")
        db.ws(ws="SheetA").update_index(row=1, col=2, val="beta_header")
        db.ws(ws="SheetA").update_index(row=2, col=1, val="a1")
        db.ws(ws="SheetA").update_index(row=2, col=2, val="b1")
        db.add_ws(ws="SheetB")
        db.ws(ws="SheetB").update_index(row=1, col=1, val="gamma_header")
        db.ws(ws="SheetB").update_index(row=1, col=2, val="delta_header")
        db.ws(ws="SheetB").update_index(row=2, col=1, val="c1")
        db.ws(ws="SheetB").update_index(row=2, col=2, val="d1")
        xl.writexl(db=db, fn=TWO_SHEET_XLSX)
        try:
            path = CsvPath()
            path.config.cache_dir_path = CACHE_DIR
            cacher = LinesAndHeadersCacher(path)
            headers_a = cacher.get_original_headers(f"{TWO_SHEET_XLSX}#SheetA")
            headers_b = cacher.get_original_headers(f"{TWO_SHEET_XLSX}#SheetB")
            assert headers_a == ["alpha_header", "beta_header"]
            assert headers_b == ["gamma_header", "delta_header"]
        finally:
            Nos(TWO_SHEET_XLSX).remove()
