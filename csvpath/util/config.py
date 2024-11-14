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
    PRINT = "print"


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
    FUNCTIONS = "functions"
    CACHE = "cache"


class Config:
    """by default finds config files at ./config/config.ini.
    To set a different location:
     - set a CSVPATH_CONFIG_FILE env var
     - create a Config instance set its CONFIG member and call reload
     - or set Config.CONFIG and reload to reset all instances w/o own specific settings
    Also, you can pass Config(load=False) to give you the opportunity to set some/all
    properties programmatically.
    """

    CONFIG: str = "config/config.ini"
    CSVPATH_CONFIG_FILE_ENV: str = "CSVPATH_CONFIG_PATH"

    def __init__(self, *, load=True):
        self.load = load
        self._cache_dir_path = None
        self._function_imports = None
        self._csvpath_file_extensions = None
        self._csv_file_extensions = None
        self._csvpath_errors_policy = None
        self._csvpaths_errors_policy = None
        self._csvpath_log_level = None
        self._csvpaths_log_level = None
        self._log_file = None
        self._log_files_to_keep = None
        self._log_file_size = None
        self._archive_path = None
        self._inputs_files_path = None
        self._inputs_csvpaths_path = None
        self._config = RawConfigParser()
        self.log_file_handler = None
        self._configpath = environ.get(Config.CSVPATH_CONFIG_FILE_ENV)
        if self._configpath is None:
            self._configpath = Config.CONFIG
        if self.load:
            self._load_config()

    @property
    def load(self) -> bool:
        return self._load

    @load.setter
    def load(self, lo: bool) -> None:
        self._load = lo

    def reload(self):
        self._config = RawConfigParser()
        self._load = True
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
            print(
                f"WARNING: Check config at {self.config_path} for [{section}][{name}]"
            )

    def add_to_config(self, section, key, value) -> None:
        if not self._config.has_section(section):
            self._config.add_section(section)
        self._config.set(section, key, value)
        self.save_config()

    def save_config(self) -> None:
        with open(self.configpath, "w") as f:
            self._config.write(f)

    def _create_default_config(self) -> None:
        directory = ""
        name = ""
        if self._configpath is None or self._configpath.strip() == "":
            raise ConfigurationException("Config path cannot be None")
        if self._configpath.find(os.sep) > 0:
            s = self._configpath.rfind(os.sep)
            directory = self._configpath[0:s]
            name = self._configpath[s + 1 :]
        if directory != "":
            if not path.exists(directory):
                os.makedirs(directory)
        with open(self._configpath, "w", encoding="utf-8") as file:
            c = """
[csvpath_files]
extensions = txt, csvpath, csvpaths
[csv_files]
extensions = txt, csv, tsv, dat, tab, psv, ssv
[errors]
csvpath = raise, collect, stop, fail, print
csvpaths = raise, collect
[logging]
csvpath = info
csvpaths = info
log_file = logs/csvpath.log
log_files_to_keep = 100
log_file_size = 52428800
[config]
path =
[functions]
imports =
[cache]
path =
[results]
archive = archive
[inputs]
files = inputs/named_files
csvpaths = inputs/named_paths
            """
            file.write(c)
            print(f"Created a default config file at {directory} with name {name}.")
            print("If you want your config to be somewhere else remember to")
            print("update the path in the default config.ini")

    def _assure_logs_path(self) -> None:
        if self.load:
            filepath = self.log_file
            if not filepath or filepath.strip() == "":
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

    def _assure_archive_path(self) -> None:
        if self.load:
            if self.archive_path is None or self.archive_path.strip() == "":
                self.archive_path = "archive"
            if not path.exists(self.archive_path):
                os.makedirs(self.archive_path)

    def _assure_inputs_files_path(self) -> None:
        if self.load:
            if self.inputs_files_path is None or self.inputs_files_path.strip() == "":
                self.inputs_files_path = "inputs/named_files"
            if not path.exists(self.inputs_files_path):
                os.makedirs(self.inputs_files_path)

    def _assure_inputs_csvpaths_path(self) -> None:
        if self.load:
            if (
                self.inputs_csvpaths_path is None
                or self.inputs_csvpaths_path.strip() == ""
            ):
                self.inputs_csvpaths_path = "inputs/named_paths"
            if not path.exists(self.inputs_csvpaths_path):
                os.makedirs(self.inputs_csvpaths_path)

    def _assure_cache_path(self) -> None:
        if self.load:
            if self.cache_dir_path is None or self.cache_dir_path.strip() == "":
                self.cache_dir_path = "cache"
            if not path.exists(self.cache_dir_path):
                os.makedirs(self.cache_dir_path)

    def _assure_config_file_path(self) -> None:
        if self.load:
            if not self._configpath or self._configpath.strip() == "":
                self._configpath = Config.CONFIG
            if not os.path.isfile(self._configpath):
                self._create_default_config()

    def _load_config(self, norecurse=False):
        if self._load is False:
            print(
                "WARNING: _load_config called on a config instance that is set to not load"
            )
            return
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
        # path to external functions list. external functions are very optional.
        # not blowing up when absent seems reasonable.
        try:
            self.function_imports = self._get(Sections.FUNCTIONS.value, "imports")
        except Exception:
            print(
                "WARNING: config cannot load [functions][imports] from {self.configpath}"
            )
            pass
        # likewise caching.
        try:
            self.cache_dir_path = self._get(Sections.CACHE.value, "path")
        except Exception:
            print("WARNING: config cannot load [cache][path] from {self.configpath}")
            pass
        #
        # reload if another config path is set
        #
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
        #
        # make sure a cache dir exists. the default should be chosen in the
        # default config, but regardless, we create the dir.
        #
        self._assure_cache_path()
        #
        # make sure a inputs dirs exist.
        #
        self._assure_inputs_files_path()
        self._assure_inputs_csvpaths_path()

    # ======================================

    @property
    def configpath(self) -> str:
        return self._configpath

    @configpath.setter
    def configpath(self, path: str) -> None:
        self._configpath = path

    @property
    def cache_dir_path(self) -> str:
        return self._cache_dir_path

    @cache_dir_path.setter
    def cache_dir_path(self, p) -> None:
        self._cache_dir_path = p

    @property
    def archive_path(self) -> str:
        if self._archive_path is None:
            self._archive_path = self._get("results", "archive")
            if self._archive_path is None:
                self._archive_path = "archive"
                self.add_to_config("results", "archive", "archive")
        return self._archive_path

    @archive_path.setter
    def archive_path(self, p) -> None:
        self._archive_path = p

    @property
    def inputs_files_path(self) -> str:
        if self._inputs_files_path is None:
            self._inputs_files_path = self._get("inputs", "files")
            if self._inputs_files_path is None:
                self._inputs_files_path = "inputs"
                self.add_to_config("inputs", "files", "inputs/named_files")
        return self._inputs_files_path

    @inputs_files_path.setter
    def inputs_files_path(self, p) -> None:
        self._inputs_files_path = p

    @property
    def inputs_csvpaths_path(self) -> str:
        if self._inputs_csvpaths_path is None:
            self._inputs_csvpaths_path = self._get("inputs", "csvpaths")
            if self._inputs_csvpaths_path is None:
                self._inputs_csvpaths_path = "inputs"
                self.add_to_config("inputs", "csvpaths", "inputs/named_paths")
        return self._inputs_csvpaths_path

    @inputs_csvpaths_path.setter
    def inputs_csvpaths_path(self, p) -> None:
        self._inputs_csvpaths_path = p

    @property
    def function_imports(self) -> str:
        return self._function_imports

    @function_imports.setter
    def function_imports(self, path: str) -> None:
        self._function_imports = path

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
