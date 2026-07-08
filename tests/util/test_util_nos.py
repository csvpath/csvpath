import unittest
from csvpath.util.nos import Nos

from csvpath.managers.server_config import ServerConfig
from csvpath.managers.files.file_descriptor import Config

from tests.csvpaths.builder import Builder
from csvpath.util.var_utility import VarUtility as vaut
from csvpath.util.file_writers import DataFileWriter


class TestUtilNos(unittest.TestCase):
    def test_nos_server_config_1(self) -> None:
        paths = Builder().build()
        #
        # get the usual creds, server port, and a path
        #
        server = vaut.parse_var_value(paths.config, "server", "SFTP_SERVER")
        port = vaut.parse_var_value(paths.config, "port", "SFTP_PORT")
        username = vaut.parse_var_value(paths.config, "username", "SFTP_USER")
        password = vaut.parse_var_value(paths.config, "password", "SFTP_PASSWORD")

        path = f"sftp://{server}:{port}/nos_test.txt"
        #
        # put a file so we're sure
        #
        with DataFileWriter(path=path, mode="w") as file:
            file.write("dummy text")
        #
        # make sure there is no backend sftp config
        #
        paths.config.set(section="sftp", name="server", value="")
        paths.config.set(section="sftp", name="port", value="")
        paths.config.set(section="sftp", name="username", value="")
        paths.config.set(section="sftp", name="password", value="")

        assert paths.config.get(section="sftp", name="password") in [None, ""]
        #
        # setup a server creds
        #
        sc = Config(
            sources={
                "test": ServerConfig(
                    address=server,
                    port=port,
                    username=username,
                    password=password,
                )
            }
        )
        nos = Nos(path)
        nos.server_config = sc.sources
        assert nos.is_sftp
        assert nos.isfile()
        path = f"sftp://{server}:{port}/never_gonna_catch_me.txt"
        nos.path = path
        assert nos.is_sftp
        assert not nos.isfile()

    def test_location(self):
        assert Nos("https://localhost:8080/a").location == "localhost:8080"
        assert Nos("https://localhost:8080/a").location_and_port == ("localhost", 8080)
        assert Nos("sftp://localhost:2022/a").location_and_port == ("localhost", 2022)
        assert Nos("azure://blob/a").location_and_port == ("blob", None)

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
