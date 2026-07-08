import unittest
import os
from csvpath.util.path_util import PathUtility as pathu


class TestUtilPathUtil(unittest.TestCase):
    def test_path_util_location(self):
        assert pathu.location("sftp://aserver/afile.txt") == "aserver"
        assert pathu.location("sftp://aserver:2022/afile.txt") == "aserver:2022"
        assert pathu.location("aserver/afile.txt") is None
        assert pathu.location("afile.txt") is None

    def test_path_util_location_and_port(self):
        assert pathu.location_and_port("sftp://aserver/afile.txt") == ("aserver", None)
        assert pathu.location_and_port("sftp://aserver:2022/afile.txt") == (
            "aserver",
            "2022",
        )
        assert pathu.location_and_port("aserver/afile.txt") is None
        assert pathu.location_and_port("afile.txt") is None

    def test_path_util_dir_name(self):
        assert pathu.dir_name("/a/b/c.txt") == "/a/b"
        assert pathu.dir_name("c.txt") == ""
        assert pathu.dir_name("https://f/i/s.html") == "https://f/i"
        assert pathu.dir_name("\\a\\b\\c.txt") == "\\a\\b"
        assert pathu.dir_name("d:\\a\\b\\c.txt") == "d:\\a\\b"

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
