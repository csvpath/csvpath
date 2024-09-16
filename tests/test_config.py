import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.util.config_exception import ConfigurationException


class TestConfig(unittest.TestCase):
    def test_config_assure_log_dir(self):
        path = CsvPath()
        config = path.config
        dirpath = config._get_dir_path("tests/test_resources/config-1/config-1.ini")
        print(f"test_config_assure_log_dir: dirpath: {dirpath}")
        assert dirpath == "tests/test_resources/config-1"

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

    def test_config2(self):
        path = CsvPath()
        config = path.config

        #
        # CSVPATH FILES
        #
        with pytest.raises(ConfigurationException):
            config.csvpath_file_extensions = None
            config.validate_config()
        #
        # should work because the @property will list it
        #
        config.csvpath_file_extensions = "txt"
        config.validate_config()
        #
        # can't be empty
        #
        with pytest.raises(ConfigurationException):
            config.csvpath_file_extensions = []
            config.validate_config()
        config.csvpath_file_extensions = ["csvpaths", "csvpath"]
        #
        # CSV FILES
        #
        with pytest.raises(ConfigurationException):
            config.csv_file_extensions = None
            config.validate_config()
        #
        # should work because the @property will list it
        #
        config.csv_file_extensions = "txt"
        config.validate_config()
        #
        # can't be empty
        #
        with pytest.raises(ConfigurationException):
            config.csv_file_extensions = []
            config.validate_config()
        config.csv_file_extensions = ["csv", "tsv"]

        #
        # CSVPATH ERROR POLICY
        #
        with pytest.raises(ConfigurationException):
            config.csvpath_errors_policy = None
            config.validate_config()
        #
        # should work because the @property will list it
        #
        config.csvpath_errors_policy = "stop"
        config.validate_config()
        #
        # can't be empty
        #
        with pytest.raises(ConfigurationException):
            config.csvpath_errors_policy = []
            config.validate_config()
        #
        # can't be wrong
        #
        with pytest.raises(ConfigurationException):
            config.csvpath_errors_policy = ["fish"]
            config.validate_config()
        config.csvpath_errors_policy = ["raise", "collect"]

        #
        # CSVPATHS ERROR POLICY
        #
        with pytest.raises(ConfigurationException):
            config.csvpaths_errors_policy = None
            config.validate_config()
        #
        # should work because the @property will list it
        #
        config.csvpaths_errors_policy = "stop"
        config.validate_config()
        #
        # can't be empty
        #
        with pytest.raises(ConfigurationException):
            config.csvpaths_errors_policy = []
            config.validate_config()
        #
        # can't be wrong
        #
        with pytest.raises(ConfigurationException):
            config.csvpaths_errors_policy = ["fish"]
            config.validate_config()
        config.csvpaths_errors_policy = ["raise", "collect"]

        #
        # CSVPATH LOG LEVEL
        #
        with pytest.raises(ConfigurationException):
            config.csvpath_log_level = None
            config.validate_config()
        #
        # can't be number
        #
        with pytest.raises(ConfigurationException):
            config.csvpath_log_level = 1
            config.validate_config()
        #
        # can't be wrong
        #
        with pytest.raises(ConfigurationException):
            config.csvpath_log_level = "wombat"
            config.validate_config()
        config.csvpath_log_level = "error"

        #
        # CSVPATHS LOG LEVEL
        #
        with pytest.raises(ConfigurationException):
            config.csvpaths_log_level = None
            config.validate_config()
        #
        # can't be number
        #
        with pytest.raises(ConfigurationException):
            config.csvpaths_log_level = 1
            config.validate_config()
        #
        # can't be wrong
        #
        with pytest.raises(ConfigurationException):
            config.csvpaths_log_level = "wombat"
            config.validate_config()
        config.csvpaths_log_level = "error"

        #
        # LOG FILE
        #
        with pytest.raises(ConfigurationException):
            config.log_file = None
            config.validate_config()
        #
        # can't be number
        #
        with pytest.raises(ConfigurationException):
            config.log_file = 1
            config.validate_config()
        config.log_file = "/log"

        #
        # LOG FILES TO KEEP
        #
        with pytest.raises(ConfigurationException):
            config.log_files_to_keep = None
            config.validate_config()
        #
        # must be a number
        #
        with pytest.raises(ConfigurationException):
            config.log_files_to_keep = "one"
            config.validate_config()
        config.log_files_to_keep = 5

        #
        # LOG FILES SIZE
        #
        with pytest.raises(ConfigurationException):
            config.log_file_size = None
            config.validate_config()
        #
        # must be a number
        #
        with pytest.raises(ConfigurationException):
            config.log_file_size = "one"
            config.validate_config()
        config.log_file_size = 50
