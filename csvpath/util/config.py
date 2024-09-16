from configparser import RawConfigParser
from dataclasses import dataclass
from os import path, environ
import os
from typing import Dict, List
from enum import Enum
import logging
from ..util.config_exception import ConfigurationException

#
#   1 csvpaths & csvpath own their own config
#   2 start up to sensible defaults in config.ini
#   3 reloading is easy
#   4 programmatically changing values is easy
#   5 config validation is easy
#


class OnError(Enum):
    RAISE = "raise"
    QUIET = "quiet"
    COLLECT = "collect"
    STOP = "stop"
    FAIL = "fail"


class LogLevels(Enum):
    INFO = "info"
    DEBUG = "debug"
    WARN = "warn"
    ERROR = "error"


class LogFile(Enum):
    LOG_FILE = "log_file"
    LOG_FILES_TO_KEEP = "log_files_to_keep"
    LOG_FILE_SIZE = "log_file_size"


class Sections(Enum):
    CSVPATH_FILES = "csvpath_files"
    CSV_FILES = "csv_files"
    ERRORS = "errors"
    LOGGING = "logging"


class CsvPathConfig:
    """by default finds config files at ./config/config.ini.
    To set a different location:
     - set a CSVPATH_CONFIG_FILE env var
     - create a CsvPathConfig instance set its CONFIG member and call reload
     - or set CsvPathConfig.CONFIG and reload to reset all instances w/o own specific settings
    """

    CONFIG: str = "config/config.ini"
    CSVPATH_CONFIG_FILE_ENV: str = "CSVPATH_CONFIG_PATH"

    def __init__(self, holder):
        self._holder = holder
        self._config = RawConfigParser()
        self.log_file_handler = None
        self._configpath = environ.get(CsvPathConfig.CSVPATH_CONFIG_FILE_ENV)
        if self._configpath is None:
            self._configpath = CsvPathConfig.CONFIG
        self._load_config()

    def reload(self):
        self._config = RawConfigParser()
        self._load_config()

    def set_config_path_and_reload(self, path: str) -> None:
        self._configpath = path
        self.reload()

    @property
    def config_path(self) -> str:
        return self._configpath

    def _get(self, section: str, name: str):
        if self._config is None:
            raise ConfigurationException("No config object available")
        try:
            s = self._config[section][name]
            s = s.strip()
            ret = None
            if s.find(",") > -1:
                ret = [s.strip() for s in s.split(",")]
            else:
                ret = s
            return ret
        except KeyError:
            raise ConfigurationException(
                f"Check config at {self.config_path} for [{section}][{name}]"
            )

    def _create_default_config(self) -> None:
        if not path.exists("config"):
            os.makedirs("config")
            with open(CsvPathConfig.CONFIG, "w") as file:
                c = """
[csvpath_files]
extensions = txt, csvpath, csvpaths
[csv_files]
extensions = txt, csv, tsv, dat, tab, psv, ssv
[errors]
csvpath = raise, collect, stop, fail
csvpaths = raise, collect
[logging]
csvpath = info
csvpaths = info
log_file = logs/csvpath.log
log_files_to_keep = 100
log_file_size = 52428800
[config]
path =
                """
                file.write(c)
            print(f"Creating a default config file at {CsvPathConfig.CONFIG}.")
            print("If you want your config to be somewhere else remember to")
            print("update the path in the default config.ini")

    def _assure_logs_path(self) -> None:
        filepath = self.log_file
        if not filepath:
            filepath = "logs/csvpath.log"
            self.log_file = filepath
        dirpath = self._get_dir_path(filepath)
        if dirpath and not path.exists(dirpath):
            os.makedirs(dirpath)

    def _get_dir_path(self, filepath):
        if filepath.find(os.sep) > -1:
            dirpath = filepath[0 : filepath.rfind(os.sep)]
            return dirpath
        return None

    def _assure_config_file_path(self) -> None:
        if not self._configpath or not os.path.isfile(self._configpath):
            self._configpath = CsvPathConfig.CONFIG
            self._create_default_config()

    def _load_config(self, norecurse=False):
        self._assure_config_file_path()
        #
        #
        #
        self._config.read(self._configpath)
        self.csvpath_file_extensions = self._get(
            Sections.CSVPATH_FILES.value, "extensions"
        )
        self.csv_file_extensions = self._get(Sections.CSV_FILES.value, "extensions")

        self.csvpath_errors_policy = self._get(Sections.ERRORS.value, "csvpath")
        self.csvpaths_errors_policy = self._get(Sections.ERRORS.value, "csvpaths")

        self.csvpath_log_level = self._get(Sections.LOGGING.value, "csvpath")
        self.csvpaths_log_level = self._get(Sections.LOGGING.value, "csvpaths")

        self.log_file = self._get(Sections.LOGGING.value, LogFile.LOG_FILE.value)
        self.log_files_to_keep = self._get(
            Sections.LOGGING.value, LogFile.LOG_FILES_TO_KEEP.value
        )
        self.log_file_size = self._get(
            Sections.LOGGING.value, LogFile.LOG_FILE_SIZE.value
        )
        path = self._get("config", "path")
        if path:
            path = path.strip().lower()
        if path and path != "" and path != self._configpath.strip().lower():
            self._configpath = path
            self.reload()
            return
        self.validate_config()

    def validate_config(self) -> None:
        #
        # files
        #
        if (
            self.csvpath_file_extensions is None
            or not isinstance(self.csvpath_file_extensions, list)
            or not len(self.csvpath_file_extensions) > 0
        ):
            raise ConfigurationException(
                f"CsvPath file extensions are wrong: {self.csvpath_file_extensions}"
            )
        if (
            self.csv_file_extensions is None
            or not isinstance(self.csv_file_extensions, list)
            or not len(self.csv_file_extensions) > 0
        ):
            raise ConfigurationException("CSV file extensions are wrong")
        #
        # error policies
        #
        if (
            self.csvpath_errors_policy is None
            or not isinstance(self.csvpath_errors_policy, list)
            or not len(self.csvpath_errors_policy) > 0
        ):
            raise ConfigurationException("CsvPath error policy is wrong")
        for _ in self.csvpath_errors_policy:
            if _ not in OnError:
                raise ConfigurationException(f"CsvPath error policy {_} is wrong")
        if (
            self.csvpaths_errors_policy is None
            or not isinstance(self.csvpaths_errors_policy, list)
            or not len(self.csvpaths_errors_policy) > 0
        ):
            raise ConfigurationException("CsvPaths error policy is wrong")
        for _ in self.csvpaths_errors_policy:
            if _ not in OnError:
                raise ConfigurationException(f"CsvPaths error policy {_} is wrong")
        #
        # log levels
        #
        if self.csvpath_log_level is None or not isinstance(
            self.csvpath_log_level, str
        ):
            raise ConfigurationException(
                f"CsvPath log level is wrong: {self.csvpath_log_level}"
            )
        if self.csvpath_log_level not in LogLevels:
            raise ConfigurationException(f"CsvPath log level {_} is wrong")
        if self.csvpaths_log_level is None or not isinstance(
            self.csvpaths_log_level, str
        ):
            raise ConfigurationException("CsvPaths log level is wrong")
        if self.csvpaths_log_level not in LogLevels:
            raise ConfigurationException(f"CsvPaths log level {_} is wrong")
        #
        # log files config
        #
        if self.log_file is None or not isinstance(self.log_file, str):
            raise ConfigurationException(f"Log file path is wrong: {self.log_file}")
        #
        # make sure the log dir exists
        #
        self._assure_logs_path()
        if self.log_files_to_keep is None or not isinstance(
            self.log_files_to_keep, int
        ):
            raise ConfigurationException(
                f"Log files to keep is wrong: {type(self.log_files_to_keep)}"
            )
        if self.log_file_size is None or not isinstance(self.log_file_size, int):
            raise ConfigurationException("Log files size is wrong")

    # ======================================

    @property
    def csvpath_file_extensions(self) -> list[str]:
        return self._csvpath_file_extensions

    @csvpath_file_extensions.setter
    def csvpath_file_extensions(self, ss: list[str]) -> None:
        if isinstance(ss, str):
            ss = [ss]
        self._csvpath_file_extensions = ss

    @property
    def csv_file_extensions(self) -> list[str]:
        return self._csv_file_extensions

    @csv_file_extensions.setter
    def csv_file_extensions(self, ss: list[str]) -> None:
        if isinstance(ss, str):
            ss = [ss]
        self._csv_file_extensions = ss

    @property
    def csvpath_errors_policy(self) -> list[str]:
        return self._csvpath_errors_policy

    @csvpath_errors_policy.setter
    def csvpath_errors_policy(self, ss: list[str]) -> None:
        if isinstance(ss, str):
            ss = [ss]
        self._csvpath_errors_policy = ss

    @property
    def csvpaths_errors_policy(self) -> list[str]:
        return self._csvpaths_errors_policy

    @csvpaths_errors_policy.setter
    def csvpaths_errors_policy(self, ss: list[str]) -> None:
        if isinstance(ss, str):
            ss = [ss]
        self._csvpaths_errors_policy = ss

    @property
    def csvpath_log_level(self) -> str:
        return self._csvpath_log_level

    @csvpath_log_level.setter
    def csvpath_log_level(self, s: str) -> None:
        self._csvpath_log_level = s

    @property
    def csvpaths_log_level(self) -> str:
        return self._csvpaths_log_level

    @csvpaths_log_level.setter
    def csvpaths_log_level(self, s: str) -> None:
        self._csvpaths_log_level = s

    @property
    def log_file(self) -> str:
        return self._log_file

    @log_file.setter
    def log_file(self, s: str) -> None:
        self._log_file = s

    @property
    def log_files_to_keep(self) -> int:
        return self._log_files_to_keep

    @log_files_to_keep.setter
    def log_files_to_keep(self, i: int) -> None:
        try:
            self._log_files_to_keep = int(i)
        except (TypeError, ValueError):
            raise ConfigurationException("Error in log_files_to_keep config")

    @property
    def log_file_size(self) -> int:
        return self._log_file_size

    @log_file_size.setter
    def log_file_size(self, i: int) -> None:
        try:
            self._log_file_size = int(i)
        except (TypeError, ValueError):
            raise ConfigurationException("Error in log_files_size config")
