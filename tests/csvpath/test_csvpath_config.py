import unittest
import pytest
import os
import json
from csvpath import CsvPath
from csvpath.util.config import Config
from csvpath.util.config_exception import ConfigurationException
from csvpath.util.nos import Nos

from csvpath.util.config_env import ConfigEnv

TEST_INI = (
    f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}deleteme{os.sep}config.ini"
)
TINI = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}config.ini"
OINI = os.getenv("CSVPATH_CONFIG_PATH")
# OINI = f"config{os.sep}config.ini"
BAD_INI = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}bad_config.ini"


class TestCsvPathConfig(unittest.TestCase):
    def test_config_env(self):
        #
        # this tests the ability to allow or disallow var sub of all caps var values
        # in system env vars or a vars json dict.
        #
        # setup a config.ini for the test
        #
        path = os.path.join("tests", "test_resources", "temp", "config.ini")
        nos = Nos(path)
        #
        # the ini should be generated when not found, we'll remove it if it already exists
        #
        if nos.exists():
            nos.remove()
        assert not nos.exists()
        csvpath = CsvPath()
        config = csvpath.config
        config.set_config_path_and_reload(path)
        #
        # we should allow var sub by default
        #
        t = config.get(section="config", name="allow_var_sub")
        assert t == "True"
        #
        # we expect to get var sub from the user's env by default
        #
        e = config.get(section="config", name="var_sub_source")
        assert e == "env"
        #
        # when not found, we default to returning the name
        #
        configenv = ConfigEnv(config=config)
        v = configenv.get(name="BLUEFISH")
        assert v == "BLUEFISH"
        #
        # but we can return a default value
        #
        v = configenv.get(name="BLUEFISH", default="ha")
        assert v == "ha"
        #
        # we make a dir for the env file, if needed, but it never be..?
        #
        path = os.path.dirname(path)
        if not Nos(path).dir_exists():
            raise RuntimeError(
                f"Why doesn't path {path} exist when we had to generate a config.ini?"
            )
        path = os.path.join(path, "env.json")
        #
        # configenv will create an empty env.json when it doesn't find it
        #
        if Nos(path).exists():
            Nos(path).remove()
        #
        # update the config so configenv knows to look to the path
        #
        config.set(section="config", name="var_sub_source", value=path)
        configenv.refresh()
        #
        # we should get our default back because the env.json file is created empty
        #
        v = configenv.get(name="BLUEFISH", default="ha")
        assert v == "ha"
        assert Nos(path).exists()
        #
        # add our env var name
        #
        with open(path, "w") as file:
            json.dump({"BLUEFISH": "ha"}, file, indent=4)
        assert Nos(path).exists()
        configenv.refresh()
        #
        # passing no default value we should still get the desired sub value
        #
        v = configenv.get(name="BLUEFISH")
        assert v == "ha"

    def test_config_no_load(self):
        config = Config(load=False)
        assert config.csvpaths_log_level is None
        config.csvpaths_log_level = "debug"
        assert config.csvpaths_log_level == "debug"
        if os.path.exists(TEST_INI):
            os.remove(TEST_INI)
        print(f"setting confgipath to: {TEST_INI}")
        config.configpath = TEST_INI
        config._create_default_config
        config.reload()
        assert config.csvpaths_log_level == "info"
        assert os.path.exists(TEST_INI)

    def test_config_default_file_by_path(self):
        oini = None
        if Config.CSVPATH_CONFIG_FILE_ENV in os.environ:
            oini = os.environ[Config.CSVPATH_CONFIG_FILE_ENV]
        try:
            os.environ[Config.CSVPATH_CONFIG_FILE_ENV] = TEST_INI
            if os.path.exists(TEST_INI):
                os.remove(TEST_INI)
            Config()
            assert os.path.exists(TEST_INI)
        finally:
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
        # assert config.CONFIG == OINI
        assert config.get(section="extensions", name="csv_files")
        assert len(config.get(section="extensions", name="csv_files")) == 6
        assert "csv" in config.get(section="extensions", name="csv_files")
        config.set_config_path_and_reload(TINI)
        assert config.config_path == TINI
        print(f"cfgasd: {config.configpath}")
        assert config.get(section="extensions", name="csv_files")
        assert len(config.get(section="extensions", name="csv_files")) == 3
        assert "before" in config.get(section="extensions", name="csv_files")
        assert "quiet" in config.csvpaths_errors_policy
        assert len(config.csvpath_errors_policy) == 1
        assert config is path.config
        with pytest.raises(ConfigurationException):
            config.set_config_path_and_reload(BAD_INI)

    def test_config2(self):
        path = CsvPath()
        config = path.config
        #
        # CSVPATH FILES
        #
        config.set(section="extensions", name="csvpath_files", value="txt")
        config.validate_config()
        #
        # CSV FILES
        #
        assert config.get(section="extensions", name="csv_files")
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
