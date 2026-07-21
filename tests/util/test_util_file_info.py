import os
import unittest
import pytest
from csvpath.util.file_info import FileInfo

TEST_FILE = os.path.join("tests", "util", "test_resources", "test.csv")


class TestUtilFileInfo(unittest.TestCase):
    def test_info_none_raises(self):
        with pytest.raises(ValueError):
            FileInfo.info(None)

    def test_info_local_file(self):
        info = FileInfo.info(TEST_FILE)
        assert info["bytes"] == os.path.getsize(TEST_FILE)
        s = os.stat(TEST_FILE)
        assert info["mode"] == s.st_mode
        assert info["device"] == s.st_dev
        assert info["created"] == s.st_ctime
        assert info["last_read"] == s.st_atime
        assert info["last_mod"] == s.st_mtime

    def test_info_remote_path_returns_empty(self):
        info = FileInfo.info("s3://some-bucket/some-key.csv")
        assert info == FileInfo._empty()

    def test_info_missing_local_file_returns_empty(self):
        info = FileInfo.info(
            os.path.join("tests", "util", "test_resources", "does_not_exist.csv")
        )
        assert info == FileInfo._empty()

    def test_empty_shape(self):
        empty = FileInfo._empty()
        assert empty == {
            "mode": "",
            "device": "",
            "bytes": -1,
            "created": None,
            "last_read": None,
            "last_mod": None,
        }

    def test_local_matches_os_stat(self):
        s = os.stat(TEST_FILE)
        meta = FileInfo._local(TEST_FILE)
        assert meta["bytes"] == s.st_size
        assert meta["mode"] == s.st_mode
