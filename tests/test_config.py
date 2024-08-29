import unittest
from csvpath.util.config import CsvPathConfig


class TestConfig(unittest.TestCase):
    def test_config1(self):
        config = CsvPathConfig()

        print(
            f"TestConfig.test_config1: config.CSVPATH_ON_ERROR: {config.CSVPATH_ON_ERROR}"
        )
        assert config.CSVPATH_ON_ERROR
        assert len(config.CSVPATH_ON_ERROR) >= 1
        assert config.CSVPATHS_ON_ERROR
        assert len(config.CSVPATHS_ON_ERROR) >= 1
        assert config.CSV_FILE_EXTENSIONS
        assert len(config.CSV_FILE_EXTENSIONS) >= 1
        assert config.CSVPATH_FILE_EXTENSIONS
        assert len(config.CSVPATH_FILE_EXTENSIONS) >= 1
        assert "csv" in config.CSV_FILE_EXTENSIONS
        assert "csvpath" in config.CSVPATH_FILE_EXTENSIONS
        print(f"TestConfig.test_config1: config is {config}")

    def test_config2(self):
        config = CsvPathConfig()
        config.CONFIG = "tests/test_resources/config.ini"
        config.reload()
        assert config.CSVPATH_ON_ERROR
        assert len(config.CSVPATH_ON_ERROR) == 1
        assert config.CSVPATHS_ON_ERROR
        assert len(config.CSVPATHS_ON_ERROR) == 1
        assert config.CSV_FILE_EXTENSIONS
        assert len(config.CSV_FILE_EXTENSIONS) > 1
        assert config.CSVPATH_FILE_EXTENSIONS
        assert len(config.CSVPATH_FILE_EXTENSIONS) == 1
        assert "seen" in config.CSV_FILE_EXTENSIONS
        assert "never" in config.CSVPATH_FILE_EXTENSIONS
        assert ["quiet"] == config.CSVPATH_ON_ERROR
        assert ["quiet"] == config.CSVPATHS_ON_ERROR
