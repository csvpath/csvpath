from configparser import RawConfigParser
from dataclasses import dataclass
from os import path, environ
from typing import Dict, List
from enum import Enum
import logging
from ..util.config_exception import ConfigurationException


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


# @dataclass
class CsvPathConfig:
    """by default finds config files at ./config/config.ini.
    To set a different location:
    - set a CSVPATH_CONFIG_FILE env var
    - create a CsvPathConfig instance set its CONFIG member and call reload
    - or set CsvPathConfig.CONFIG and reload to reset all instances w/o own specific settings
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
    DEFAULT_CSVPATH_LOG_LEVEL = LogLevels.ERROR.value
    DEFAULT_CSVPATHS_LOG_LEVEL = LogLevels.ERROR.value
    DEFAULT_LOG_FILE = "./logs/csvpath.log"
    DEFAULT_LOG_FILES_TO_KEEP = 1
    DEFAULT_LOG_FILE_SIZE = 2048
    CONFIG_INSTANCE = RawConfigParser()

    def __init__(self):
        self.options: Dict[str, str] = {}
        self.CSVPATH_ON_ERROR: List[str] = []
        self.CSVPATHS_ON_ERROR: List[str] = []
        self.CSV_FILE_EXTENSIONS: List[str] = []
        self.CSVPATH_FILE_EXTENSIONS: List[str] = []
        self.CSVPATH_LOG_LEVEL = CsvPathConfig.DEFAULT_CSVPATH_LOG_LEVEL
        self.CSVPATHS_LOG_LEVEL = CsvPathConfig.DEFAULT_CSVPATHS_LOG_LEVEL
        self.LOG_FILE = CsvPathConfig.DEFAULT_LOG_FILE
        self.LOG_FILES_TO_KEEP = CsvPathConfig.DEFAULT_LOG_FILES_TO_KEEP
        self.LOG_FILE_SIZE = CsvPathConfig.DEFAULT_LOG_FILE_SIZE
        configpath = environ.get(CsvPathConfig.CSVPATH_CONFIG_FILE)
        self.log_file_handler = None
        if configpath is not None:
            self.CONFIG = configpath.strip()
        self._load_config()

    def _get(self, section: str, name: str) -> str:
        return CsvPathConfig.CONFIG_INSTANCE[section][name]

    def reload(self):
        self._load_config()

    def _load_config(self):
        if path.isfile(self.CONFIG):
            CsvPathConfig.CONFIG_INSTANCE.read(self.CONFIG)
            try:
                exts = self._get(Sections.CSVPATH_FILES.value, "extensions")
                if exts is None or len(exts.strip()) == 0:
                    exts = CsvPathConfig.DEFAULT_CSVPATH_FILE_EXTENSIONS
                self.CSVPATH_FILE_EXTENSIONS = [
                    _.strip().lower() for _ in exts.split(",")
                ]
            except KeyError:
                raise Exception(
                    f"Config failed on {Sections.CSVPATH_FILES.value}[extensions]: {self._config}"
                )

            try:
                exts = self._get(Sections.CSV_FILES.value, "extensions")
                if exts is None or len(exts.strip()) == 0:
                    exts = CsvPathConfig.DEFAULT_CSV_FILE_EXTENSIONS
                self.CSV_FILE_EXTENSIONS = [_.strip().lower() for _ in exts.split(",")]
            except KeyError:
                raise Exception(
                    f"Config failed on {Sections.CSV_FILES.value}[extensions]"
                )

            try:
                exts = self._get(Sections.ERRORS.value, "csvpath")
                if exts is None or len(exts.strip()) == 0:
                    exts = CsvPathConfig.DEFAULT_CSVPATH_ON_ERROR
                self.CSVPATH_ON_ERROR = [_.strip().lower() for _ in exts.split(",")]
            except KeyError:
                raise Exception(f"Config failed on {Sections.ERRORS.value}[csvpath]")
            for _ in self.CSVPATH_ON_ERROR:
                if _ not in OnError:
                    raise Exception(
                        f"Config failed on unknown CsvPath error option '{_}'"
                    )
            try:
                exts = self._get(Sections.ERRORS.value, "csvpaths")
                if exts is None or len(exts.strip()) == 0:
                    exts = CsvPathConfig.DEFAULT_CSVPATHS_ON_ERROR
                self.CSVPATHS_ON_ERROR = [_.strip().lower() for _ in exts.split(",")]
            except KeyError:
                raise Exception(f"Config failed on {Sections.ERRORS.value}[csvpaths]")
            for _ in self.CSVPATHS_ON_ERROR:
                if _ not in OnError:
                    raise Exception(
                        f"Config failed on unknown CsvPaths error option '{_}'"
                    )
            self._set_log_levels()
        else:
            print(f"No config file at {self.CONFIG}. Using hardcoded defaults.")

    def _set_log_levels(self):
        level = self._get(Sections.LOGGING.value, "csvpath")
        if level and level.strip() != "":
            self.CSVPATH_LOG_LEVEL = level.strip().lower()
        level = self._get(Sections.LOGGING.value, "csvpaths")
        if level and level.strip() != "":
            self.CSVPATHS_LOG_LEVEL = level.strip().lower()
        log_file = self._get(Sections.LOGGING.value, "log_file")
        if log_file and log_file.strip() != "":
            self.LOG_FILE = log_file.strip().lower()
        log_files_to_keep = self._get(Sections.LOGGING.value, "log_files_to_keep")
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
                self.LOG_FILES_TO_KEEP = CsvPathConfig.DEFAULT_LOG_FILES_TO_KEEP

        log_file_size = self._get(Sections.LOGGING.value, "log_file_size")
        if log_file_size and log_file_size.strip() != "":
            try:
                i = int(log_file_size.strip().lower())
                if i > 0:
                    self.LOG_FILE_SIZE = i
            except Exception:
                print("[log_file_size] must be an integer. Using the default.")
                self.LOG_FILE_SIZE = CsvPathConfig.DEFAULT_LOG_FILE_SIZE
