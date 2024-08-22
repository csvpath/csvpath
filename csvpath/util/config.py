from configparser import RawConfigParser
from dataclasses import dataclass
from os import path, environ
from typing import Dict, List

from csvpath import ConfigurationException
from enum import Enum


class OnError(Enum):
    RAISE = "raise"
    QUIET = "quiet"
    COLLECT = "collect"
    STOP = "stop"
    FAIL = "fail"


class Sections(Enum):
    CSVPATH_FILES = "csvpath_files"
    CSV_FILES = "csv_files"
    ERRORS = "errors"


@dataclass
class CsvPathConfig:
    """by default finds config files at ./config/config.ini.
    To set a different location:
    - set a CSVPATH_CONFIG_FILE env var
    - create a CsvPathConfig instance set its CONFIG member and call reload
    """

    CONFIG: str = "config/config.ini"
    DEFAULT_CSV_FILE_EXTENSIONS = "csv,tsv,psv,dat,ssv,txt"
    DEFAULT_CSVPATH_FILE_EXTENSIONS = "txt,csvpaths"
    DEFAULT_CSVPATH_ON_ERROR = "raise,stop"
    DEFAULT_CSVPATHS_ON_ERROR = "quiet,collect,fail"
    CSVPATH_CONFIG_FILE = "CSVPATH_CONFIG_FILE"

    def __post_init__(self):
        self.options: Dict[str, str] = {}
        self._config = RawConfigParser()

        self.CSVPATH_ON_ERROR: List[str] = []
        self.CSVPATHS_ON_ERROR: List[str] = []
        self.CSV_FILE_EXTENSIONS: List[str] = []
        self.CSVPATH_FILE_EXTENSIONS: List[str] = []

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
                self.CSVPATH_FILE_EXTENSIONS = [_.strip() for _ in exts.split(",")]
            except KeyError:
                raise ConfigurationException(
                    f"Config failed on {Sections.CSVPATH_FILES.value}[extensions]"
                )

            try:
                exts = self._config[Sections.CSV_FILES.value]["extensions"]
                if exts is None or len(exts.strip()) == 0:
                    exts = self.DEFAULT_CSV_FILE_EXTENSIONS
                self.CSV_FILE_EXTENSIONS = [_.strip() for _ in exts.split(",")]
            except KeyError:
                raise ConfigurationException(
                    f"Config failed on {Sections.CSV_FILES.value}[extensions]"
                )

            try:
                exts = self._config[Sections.ERRORS.value]["csvpath"]
                if exts is None or len(exts.strip()) == 0:
                    exts = self.DEFAULT_CSVPATH_ON_ERROR
                self.CSVPATH_ON_ERROR = [_.strip() for _ in exts.split(",")]
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
                self.CSVPATHS_ON_ERROR = [_.strip() for _ in exts.split(",")]
            except KeyError:
                raise ConfigurationException(
                    f"Config failed on {Sections.ERRORS.value}[csvpaths]"
                )
            for _ in self.CSVPATHS_ON_ERROR:
                if _ not in OnError:
                    raise ConfigurationException(
                        f"Config failed on unknown CsvPaths error option '{_}'"
                    )

        else:
            print(
                f"No config file at {self.CONFIG}. Using hardcoded defaults external to this class."
            )
