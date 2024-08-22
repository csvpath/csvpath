from configparser import RawConfigParser
from dataclasses import dataclass
from os import path, environ
from typing import Dict, List, Callable
from enum import Enum
import logging
from logging.handlers import RotatingFileHandler

from csvpath import ConfigurationException


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
    DEFAULT_LOG_FILE = "./logs/csvpath.log"
    DEFAULT_LOG_FILES_TO_KEEP = 1
    DEFAULT_LOG_FILE_SIZE = 2048

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
        self.LOG_FILE = self.DEFAULT_LOG_FILE
        self.LOG_FILES_TO_KEEP = self.DEFAULT_LOG_FILES_TO_KEEP
        self.LOG_FILE_SIZE = self.DEFAULT_LOG_FILE_SIZE
        configpath = environ.get(CsvPathConfig.CSVPATH_CONFIG_FILE)
        self.log_file_handler = None
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
        log_file = self._config[Sections.LOGGING.value]["log_file"]
        if log_file and log_file.strip() != "":
            self.LOG_FILE = log_file.strip().lower()
        log_files_to_keep = self._config[Sections.LOGGING.value]["log_files_to_keep"]
        if log_files_to_keep and log_files_to_keep.strip() != "":
            i = -1
            try:
                i = int(log_files_to_keep.strip().lower())
            except Exception:
                pass
            if i > 0 and i < 101:
                self.LOG_FILES_TO_KEEP = i
            else:
                print("[log_files_to_keep] must be between 1-100. Using the default.")
                self.LOG_FILES_TO_KEEP = self.DEFAULT_LOG_FILES_TO_KEEP

        log_file_size = self._config[Sections.LOGGING.value]["log_file_size"]
        if log_file_size and log_file_size.strip() != "":
            try:
                i = int(log_file_size.strip().lower())
                if i > 0:
                    self.LOG_FILE_SIZE = i
            except Exception:
                print("[log_file_size] must be an integer. Using the default.")
                self.LOG_FILE_SIZE = self.DEFAULT_LOG_FILE_SIZE

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
        if level == "error":
            level = logging.ERROR
        elif level == "warn":
            level = logging.WARNING
        elif level == "debug":
            level = logging.DEBUG
        elif level == "info":
            level = logging.INFO
        else:
            raise ConfigurationException(f"Unknown log level '{level}'")

        if self.log_file_handler is None:
            self.log_file_handler = RotatingFileHandler(
                filename=self.LOG_FILE,
                maxBytes=self.LOG_FILE_SIZE,
                backupCount=self.LOG_FILES_TO_KEEP,
            )
            formatter = logging.Formatter(
                "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
            )
            self.log_file_handler.setFormatter(formatter)

        logger = logging.getLogger(component)
        logger.addHandler(self.log_file_handler)
        logger.setLevel(level)
        return logger
