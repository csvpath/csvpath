import unittest
import pytest
from csvpath import CsvPath
from csvpath.util.config_exception import ConfigurationException


class TestConfig(unittest.TestCase):
    def test_config1(self):
        print("")
        path = CsvPath()
        config = path.config
        assert config is not None
        assert config.CONFIG == "config/config.ini"
        assert config.csv_file_extensions
        assert len(config.csv_file_extensions) == 7
        assert "csv" in config.csv_file_extensions
        print("")
        config.set_config_path_and_reload("tests/test_resources/config.ini")
        assert config.config_path == "tests/test_resources/config.ini"
        assert config.csv_file_extensions
        assert len(config.csv_file_extensions) == 3
        assert "before" in config.csv_file_extensions
        assert "quiet" in config.csvpaths_errors_policy
        assert len(config.csvpath_errors_policy) == 1

        assert config is path.config

        print("")
        with pytest.raises(ConfigurationException):
            config.set_config_path_and_reload("tests/test_resources/bad_config.ini")
