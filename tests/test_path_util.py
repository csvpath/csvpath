import unittest
from csvpath.util.path_util import PathUtility as pathu


class TestPathUtil(unittest.TestCase):
    def test_path_util_norm(self):
        path = "./csvpath/../org/i/am/a/path"
        normed = pathu.norm(path)
        assert normed
        assert normed != path
        assert normed == "org/i/am/a/path"

        path = "http://csvpath.com/test/../org/i/am/a/path"
        normed = pathu.norm(path, stripp=True)
        print(f"test_path_util_norm: normed: {normed}")
        chk = pathu.resep("org/i/am/a/path")
        normed = pathu.resep(normed)
        print(f"test_path_util_norm: chk: {chk}")
        assert normed == chk

    def test_path_util_resep(self):
        path = "http://csvpath.org/i/am/a\\path"
        re = pathu.resep(path)
        assert re == "http://csvpath.org/i/am/a/path"

        path = "c:\\\\csvpath.org/i/am/a\\path"
        re = pathu.resep(path, hint="win")
        assert re == "c:\\\\csvpath.org\\i\\am\\a\\path"

    def test_path_util_parts(self):
        path = "http://csvpath.org/i/am/a/path"
        parts = pathu.parts(path)
        assert parts == ["http", "csvpath.org", "i", "am", "a", "path"]

        path = "i/am/a/path"
        parts = pathu.parts(path)
        assert parts == ["i", "am", "a", "path"]
