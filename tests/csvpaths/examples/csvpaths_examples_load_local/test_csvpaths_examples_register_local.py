import unittest
import os
from csvpath import CsvPaths
from csvpath.util.backend_check import BackendCheck
from csvpath.util.file_writers import DataFileWriter


class TestLocalRegister(unittest.TestCase):
    def test_register_local_file(self):
        paths = CsvPaths()
        paths.config.set_config_path_and_reload(
            "tests/csvpaths/examples/csvpaths_examples_sftp/sftpgo_config.ini"
        )
        paths.config.add_to_config("inputs", "allow_local_files", False)
        name = "local_file"
        local = paths.config.get(section="inputs", name="allow_local_files")
        assert local is False

        path = os.path.join(
            "tests",
            "csvpaths",
            "examples",
            "csvpaths_examples_load_local",
            "csvs",
            "March-2024.csv",
        )
        paths.file_manager.remove_named_file(name)
        assert not paths.file_manager.has_named_file(name)

        paths.file_manager.add_named_file(name=name, path=path)
        assert not paths.file_manager.has_named_file(name)

        paths.config.add_to_config("inputs", "allow_local_files", True)
        paths.file_manager.add_named_file(name=name, path=path)
        assert paths.file_manager.has_named_file(name)

        paths.file_manager.remove_named_file(name)
