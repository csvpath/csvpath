from configparser import RawConfigParser
from dataclasses import dataclass
from os import path, environ
from typing import Dict, List, Callable
import logging

from csvpath import ConfigurationException
from enum import Enum


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


class Sections(Enum):
    CSVPATH_FILES = "csvpath_files"
    CSV_FILES = "csv_files"
    ERRORS = "errors"
    LOGGING = "logging"


@dataclass
class CsvPathConfig:
    """by default finds config files at ./config/config.ini.
    To set a different location:
    - set a CSVPATH_CONFIG_FILE env var
    - create a CsvPathConfig instance set its CONFIG member and call reload
    """

    CONFIG: str = "config/config.ini"
    CSVPATH_CONFIG_FILE = "CSVPATH_CONFIG_FILE"
    # extensions
    DEFAULT_CSV_FILE_EXTENSIONS = "csv,tsv,psv,dat,ssv,txt"
    DEFAULT_CSVPATH_FILE_EXTENSIONS = "txt,csvpaths"
    # errors
    DEFAULT_CSVPATH_ON_ERROR = f"{OnError.RAISE.value},{OnError.STOP.value}"
    DEFAULT_CSVPATHS_ON_ERROR = (
        "{OnError.QUIET.value},{OnError.COLLECT.value},{OnError.FAIL.value}"
    )
    # logging
    DEFAULT_CSVPATH_LOG_LEVEL = LogLevels.INFO.value
    DEFAULT_CSVPATHS_LOG_LEVEL = LogLevels.INFO.value
    DEFAULT_MATCHER_LOG_LEVEL = LogLevels.INFO.value
    DEFAULT_SCANNER_LOG_LEVEL = LogLevels.INFO.value

    def __post_init__(self):
        self.options: Dict[str, str] = {}
        self._config = RawConfigParser()
        self.CSVPATH_ON_ERROR: List[str] = []
        self.CSVPATHS_ON_ERROR: List[str] = []
        self.CSV_FILE_EXTENSIONS: List[str] = []
        self.CSVPATH_FILE_EXTENSIONS: List[str] = []
        self.CSVPATH_LOG_LEVEL = self.DEFAULT_CSVPATH_LOG_LEVEL
        self.CSVPATHS_LOG_LEVEL = self.DEFAULT_CSVPATHS_LOG_LEVEL
        self.MATCHER_LOG_LEVEL = self.DEFAULT_MATCHER_LOG_LEVEL
        self.SCANNER_LOG_LEVEL = self.DEFAULT_SCANNER_LOG_LEVEL

        configpath = environ.get(CsvPathConfig.CSVPATH_CONFIG_FILE)
        if configpath is not None:
            self.CONFIG = configpath.strip()
        self._load_config()

    def reload(self):
        self._load_config()

    def _load_config(self):
        if path.isfile(self.CONFIG):
            self._config.read(self.CONFIG)
            try:
                exts = self._config[Sections.CSVPATH_FILES.value]["extensions"]
                if exts is None or len(exts.strip()) == 0:
                    exts = self.DEFAULT_CSVPATH_FILE_EXTENSIONS
                self.CSVPATH_FILE_EXTENSIONS = [
                    _.strip().lower() for _ in exts.split(",")
                ]
            except KeyError:
                raise ConfigurationException(
                    f"Config failed on {Sections.CSVPATH_FILES.value}[extensions]"
                )

            try:
                exts = self._config[Sections.CSV_FILES.value]["extensions"]
                if exts is None or len(exts.strip()) == 0:
                    exts = self.DEFAULT_CSV_FILE_EXTENSIONS
                self.CSV_FILE_EXTENSIONS = [_.strip().lower() for _ in exts.split(",")]
            except KeyError:
                raise ConfigurationException(
                    f"Config failed on {Sections.CSV_FILES.value}[extensions]"
                )

            try:
                exts = self._config[Sections.ERRORS.value]["csvpath"]
                if exts is None or len(exts.strip()) == 0:
                    exts = self.DEFAULT_CSVPATH_ON_ERROR
                self.CSVPATH_ON_ERROR = [_.strip().lower() for _ in exts.split(",")]
            except KeyError:
                raise ConfigurationException(
                    f"Config failed on {Sections.ERRORS.value}[csvpath]"
                )
            for _ in self.CSVPATH_ON_ERROR:
                if _ not in OnError:
                    raise ConfigurationException(
                        f"Config failed on unknown CsvPath error option '{_}'"
                    )

            try:
                exts = self._config[Sections.ERRORS.value]["csvpaths"]
                if exts is None or len(exts.strip()) == 0:
                    exts = self.DEFAULT_CSVPATHS_ON_ERROR
                self.CSVPATHS_ON_ERROR = [_.strip().lower() for _ in exts.split(",")]
            except KeyError:
                raise ConfigurationException(
                    f"Config failed on {Sections.ERRORS.value}[csvpaths]"
                )
            for _ in self.CSVPATHS_ON_ERROR:
                if _ not in OnError:
                    raise ConfigurationException(
                        f"Config failed on unknown CsvPaths error option '{_}'"
                    )
            self._set_log_levels()
        else:
            print(f"No config file at {self.CONFIG}. Using hardcoded defaults.")

    def _set_log_levels(self):
        level = self._config[Sections.LOGGING.value]["csvpath"]
        if level and level.strip() != "":
            self.CSVPATH_LOG_LEVEL = level.strip().lower()
        level = self._config[Sections.LOGGING.value]["csvpaths"]
        if level and level.strip() != "":
            self.CSVPATHS_LOG_LEVEL = level.strip().lower()
        level = self._config[Sections.LOGGING.value]["matcher"]
        if level and level.strip() != "":
            self.MATCHER_LOG_LEVEL = level.strip().lower()
        level = self._config[Sections.LOGGING.value]["scanner"]
        if level and level.strip() != "":
            self.SCANNER_LOG_LEVEL = level.strip().lower()

    def get_logger(self, component: str) -> Callable:
        level = None
        if component == "csvpaths":
            level = self.CSVPATHS_LOG_LEVEL
        elif component == "csvpath":
            level = self.CSVPATH_LOG_LEVEL
        elif component == "scanner":
            level = self.SCANNER_LOG_LEVEL
        elif component == "matcher":
            level = self.MATCHER_LOG_LEVEL
        else:
            raise ConfigurationException(f"Unknown log component '{component}'")
        logger = logging.getLogger(component)
        if level == "error":
            return logger.error
        elif level == "warn":
            return logger.warn
        elif level == "debug":
            return logger.debug
        elif level == "info":
            return logger.info
        else:
            raise ConfigurationException(f"Unknown log level '{level}'")
