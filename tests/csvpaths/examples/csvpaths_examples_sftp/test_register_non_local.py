import unittest
import os


from csvpath.managers.server_config import ServerConfig
from csvpath.util.nos import Nos

from tests.csvpaths.builder import Builder
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.file_readers import DataFileReader
from csvpath.util.box import Box
from csvpath.util.var_utility import VarUtility as vaut


class TestCsvpathsExamplesSftpRegisterNonLocal(unittest.TestCase):
    def test_sftp_register_none_local_file(self):

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
        # we're going to use the local backend for this test, regardless of
        # other tests
        #
        backend = "mac" if os.sep == "/" else "windows"
        backend = os.path.join(backend, "inputs", "named_files")
        paths.config.set(section="inputs", name="files", value=backend)
        #
        # pick a name and create the named-file w/o registering any bytes
        #
        name = "s_ic"
        paths.file_manager.assure_named_file(name=name)
        #
        # make sure there is no backend sftp config
        #
        Box().empty_my_stuff()
        #
        # make sure we don't use the backend for pulling data storage
        #
        nos = Nos(path)
        if nos.do._config:
            nos.do._config.reset()
        assert not nos.do._config.has_ssh_client

        config = paths.file_manager.describer.get_config(name=name)
        #
        # setup server creds
        #
        config.sources = {
            "test": ServerConfig(
                address=server,
                port=port,
                username=username,
                password=password,
            )
        }
        paths.file_manager.describer.store_config(name, config)

        paths.file_manager.add_named_file(name=name, path=path)
        assert paths.file_manager.has_named_file(name)
        regpath = paths.file_manager.get_named_file(name)
        assert regpath
        print(f"non-local path {path} regstered at: {regpath}")
        assert regpath.startswith(f"{backend}/s_ic/nos_test.txt")
        nos = Nos(regpath)
        assert nos.exists()
        with DataFileReader(regpath) as file:
            s = file.read()
            assert s == "dummy text"
