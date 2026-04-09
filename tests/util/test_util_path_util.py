import unittest
import os
from csvpath.util.path_util import PathUtility as pathu


class TestUtilPathUtil(unittest.TestCase):
    def test_path_util_norm(self):
        path = "./csvpath/../org/i/am/a/path"
        normed = pathu.norm(path)
        assert normed
        normed = pathu.resep(normed)
        assert normed != path
        assert normed == pathu.resep("org/i/am/a/path")

        path = "http://csvpath.com/test/../org/i/am/a/path"
        normed = pathu.norm(path, stripp=True)
        normed = pathu.resep(normed)
        assert normed == pathu.resep(normed)

    def test_path_util_resep(self):
        path = "http://csvpath.org/i/am/a\\path"
        re = pathu.resep(path)
        assert re == "http://csvpath.org/i/am/a/path"

        path = "c:\\\\csvpath.org/i/am/a\\path"
        re = pathu.resep(path, hint="win")
        assert re == "c:\\\\csvpath.org\\i\\am\\a\\path"

    def test_path_util_parts_1(self):
        path = "http://csvpath.org/i/am/a/path"
        parts = pathu.parts(path)
        assert parts == ["http", "csvpath.org", "i", "am", "a", "path"]
        path = "i/am/a/path"
        parts = pathu.parts(path)
        assert parts == ["i", "am", "a", "path"]

    def test_path_util_parts_2(self):
        path = os.getcwd()
        parts = pathu.parts(path)
        assert "" not in parts
        parts2 = [str(_).strip() for _ in parts if str(_).strip() != ""]
        assert parts == parts2
