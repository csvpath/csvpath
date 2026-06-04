import unittest
from csvpath.util.nos import Nos


class TestUtilNos(unittest.TestCase):
    def test_location(self):
        assert Nos("https://localhost:8080/a").location == "localhost:8080"
        assert Nos("https://localhost:8080/a").location_and_port == ("localhost", 8080)
        assert Nos("sftp://localhost:2022/a").location_and_port == ("localhost", 2022)
        assert Nos("azure://blob/a").location_and_port == ("blob",)

    def test_nos_backends_check(self) -> None:
        assert Nos("/a/b/c").is_local
        assert not Nos("https://x/a/b/c").is_local
        assert not Nos("/a/b/c").is_http
        assert not Nos("/a/b/c").is_s3
        assert Nos("s3://a/b/c").is_s3
        assert Nos("sftp://a/b/c").is_sftp
        assert Nos("gs://a/b/c").is_gcs
        assert Nos("azure://a/b/c").is_azure
        assert Nos("http://a/b/c").is_http
