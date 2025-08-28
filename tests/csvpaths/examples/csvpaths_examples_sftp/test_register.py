import unittest
from csvpath import CsvPaths
from csvpath.util.backend_check import BackendCheck
from csvpath.util.file_writers import DataFileWriter


class TestSftpRegister(unittest.TestCase):
    def test_sftp_register_remote_file(self):
        paths = CsvPaths()
        #
        # this test is setup for sftpgo on localhost:2022 (the sftpgo default)
        #
        paths.config.set_config_path_and_reload(
            "tests/csvpaths/examples/csvpaths_examples_sftp/sftpgo_config.ini"
        )
        if BackendCheck.sftp_available(paths.config):
            name = "sftp_reg"
            server = paths.config.get(section="sftp", name="server")
            port = paths.config.get(section="sftp", name="port")
            path = f"sftp://{server}:{port}/test_sftp_register_remote_file.csv"
            paths.file_manager.remove_named_file(name)
            assert not paths.file_manager.has_named_file(name)
            with DataFileWriter(path=path) as file:
                file.write(r"test, one, two, three\nbiz, bop, bup, bat")
            paths.file_manager.add_named_file(name=name, path=path)
            assert paths.file_manager.has_named_file(name)
            paths.file_manager.remove_named_file(name)
        else:
            print("SFTP is not available. Skipping test_sftp_register_remote_file")
