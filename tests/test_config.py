import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.util.config import Config
from csvpath.util.config_exception import ConfigurationException

TEST_INI = f"tests{os.sep}test_resources{os.sep}deleteme{os.sep}config.ini"


class TestConfig(unittest.TestCase):
    def test_config_no_load(self):
        config = Config(load=False)
        assert config.csvpaths_log_level is None
        config.csvpaths_log_level = "debug"
        assert config.csvpaths_log_level == "debug"
        if os.path.exists(TEST_INI):
            os.remove(TEST_INI)
        config.configpath = TEST_INI
        config._create_default_config
        config.reload()
        assert config.csvpaths_log_level == "info"
        assert os.path.exists(TEST_INI)

    def test_config_default_file_by_path(self):
        oini = None
        if Config.CSVPATH_CONFIG_FILE_ENV in os.environ:
            oini = os.environ[Config.CSVPATH_CONFIG_FILE_ENV]
        os.environ[Config.CSVPATH_CONFIG_FILE_ENV] = TEST_INI
        if os.path.exists(TEST_INI):
            os.remove(TEST_INI)
        Config()
        assert os.path.exists(TEST_INI)
        if oini is not None:
            os.environ[Config.CSVPATH_CONFIG_FILE_ENV] = oini

    def test_config_assure_log_dir(self):
        cfg = f"tests{os.sep}test_resources{os.sep}config-1"
        path = CsvPath()
        config = path.config
        dirpath = config._get_dir_path(f"{cfg}{os.sep}config-1.ini")
        assert dirpath == cfg

    def test_config1(self):
        path = CsvPath()
        config = path.config
        assert config is not None
        assert config.CONFIG == f"config{os.sep}config.ini"
        assert config.csv_file_extensions
        assert len(config.csv_file_extensions) == 6
        assert "csv" in config.csv_file_extensions
        config.set_config_path_and_reload(
            f"tests{os.sep}test_resources{os.sep}config.ini"
        )
        assert config.config_path == f"tests{os.sep}test_resources{os.sep}config.ini"
        assert config.csv_file_extensions
        assert len(config.csv_file_extensions) == 3
        assert "before" in config.csv_file_extensions
        assert "quiet" in config.csvpaths_errors_policy
        assert len(config.csvpath_errors_policy) == 1
        assert config is path.config
        with pytest.raises(ConfigurationException):
            config.set_config_path_and_reload(
                f"tests{os.sep}test_resources{os.sep}bad_config.ini"
            )

    def test_config2(self):
        path = CsvPath()
        config = path.config
        #
        # CSVPATH FILES
        #
        #
        # should work because the @property will list it
        #
        config.csvpath_file_extensions = "txt"
        config.validate_config()
        #
        # CSV FILES
        #
        #
        # should work because the @property will list it
        #
        config.csv_file_extensions = "txt"
        config.validate_config()
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
        config.log_file = ".{os.sep}log"
