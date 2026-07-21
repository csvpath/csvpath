import hashlib
import io
import os
import unittest
from csvpath.util.hasher import Hasher
from csvpath.util.nos import Nos

TMP_DIR = os.path.join("tests", "util", "test_resources", "tmp", "hasher")
TMP_FILE = os.path.join(TMP_DIR, "sample.txt")


class TestUtilHasher(unittest.TestCase):
    def setUp(self):
        nos = Nos(TMP_DIR)
        if not nos.dir_exists():
            nos.makedirs()
        with open(TMP_FILE, "wb") as f:
            f.write(b"hello world")

    def tearDown(self):
        nos = Nos(TMP_DIR)
        if nos.dir_exists():
            nos.remove()

    def _expected_hash(self) -> str:
        return hashlib.sha256(b"hello world").hexdigest()

    def test_hash_matches_hashlib_directly(self):
        h = Hasher().hash(TMP_FILE, encode=False)
        assert h == self._expected_hash()

    def test_hash_is_stable(self):
        hasher = Hasher()
        h1 = hasher.hash(TMP_FILE, encode=False)
        h2 = hasher.hash(TMP_FILE, encode=False)
        assert h1 == h2

    def test_hash_of_file_like_object(self):
        buf = io.BytesIO(b"hello world")
        h = Hasher().hash(buf, encode=False)
        assert h == self._expected_hash()

    def test_hash_encode_percent_encodes_the_result(self):
        raw = Hasher().hash(TMP_FILE, encode=False)
        encoded = Hasher().hash(TMP_FILE, encode=True)
        assert encoded == Hasher.percent_encode(raw)

    def test_percent_encode_escapes_colon_slash_backslash(self):
        assert Hasher.percent_encode("a:b/c\\d") == "a%3Ab%2Fc%5Cd"

    def test_percent_encode_leaves_other_chars_alone(self):
        assert Hasher.percent_encode("abc123") == "abc123"
