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


#
# main external methods:
#  - load
#  - save
#  - refresh
#  - reload
#  - add_to_config
#  - get
#
class Config:
    """by default finds config files at ./config/config.ini.
    To set a different location:
     - set a CSVPATH_CONFIG_FILE env var
     - create a Config instance set its CONFIG member and call reload
     - or set Config.CONFIG and reload to reset all instances w/o own specific settings
    Also, you can pass Config(load=False) to give you the opportunity to set some/all
    properties programmatically.
    """

    CONFIG: str = f"config{os.sep}config.ini"
    CSVPATH_CONFIG_FILE_ENV: str = "CSVPATH_CONFIG_PATH"

    def __init__(self, *, load=True):
        self.load = load
        self._cache_dir_path = None
        self._function_imports = None
        self._additional_listeners = None
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
        self._transfer_root = None
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

    def get(self, *, section: str, name: str, default=None):
        return self._get(section, name, default)

    def _get(self, section: str, name: str, default=None):
        if self._config is None:
            raise ConfigurationException("No config object available")
        try:
            s = self._config[section][name]
            ret = None
            if s.find(",") > -1:
                ret = [s.strip() for s in s.split(",")]
            else:
                ret = s.strip()
            return ret
        except KeyError:
            if self.csvpath_log_level == LogLevels.DEBUG:
                print(
                    f"WARNING: Check config at {self.config_path} for [{section}][{name}]"
                )
            return default

    #
    # adds the value to the internal configparser object. doesn't save.
    # does a refresh to make sure any lists or other interpreted values
    # are up to date. if you want to save you need to call the save
    # method.
    #
    def add_to_config(self, section, key, value) -> None:
        if not self._config.has_section(section):
            self._config.add_section(section)
        #
        # values must be strings
        #
        if value is None:
            value = ""
        self._config[section][key] = value
        self.refresh()

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
            c = f"""
[csvpath_files]
extensions = txt, csvpath, csvpaths

[csv_files]
extensions = txt, csv, tsv, dat, tab, psv, ssv

[errors]
csvpath = collect, fail, print
csvpaths = raise, collect
use_format = full
pattern = {{time}}:{{file}}:{{line}}:{{paths}}:{{instance}}:{{chain}}:  {{message}}

[logging]
csvpath = info
csvpaths = info
log_file = logs{os.sep}csvpath.log
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
transfers = transfers

[inputs]
files = inputs{os.sep}named_files
csvpaths = inputs{os.sep}named_paths
on_unmatched_file_fingerprints = halt

[listeners]
# add listener group names to send events to the channel they represent
groups = default
#slack, marquez, ckan, sftp, sftpplus, otlp, sqlite

# add sqlite to capture staging, loads, and results in a local sqlite db
sqlite.results = from csvpath.managers.integrations.sqlite.sqlite_results_listener import SqliteResultsListener
sqlite.result = from csvpath.managers.integrations.sqlite.sqlite_result_listener import SqliteResultListener

# add to capture a history of all named-file stagings and all named-paths loads in
# an [inputs] files and an[inputs] paths root manifest.json
default.file = from csvpath.managers.files.files_listener import FilesListener
default.paths = from csvpath.managers.paths.paths_listener import PathsListener

# add otlp to the list of groups above to push observability metrics to an OpenTelemetry endpoint
otlp.result = from csvpath.managers.integrations.otlp.otlp_result_listener import OpenTelemetryResultListener
otlp.results = from csvpath.managers.integrations.otlp.otlp_results_listener import OpenTelemetryResultsListener
otlp.errors = from csvpath.managers.integrations.otlp.otlp_error_listener import OpenTelemetryErrorListener

# add sftp to the list of groups above to push content and metadata to an SFTP account
sftp.results = from csvpath.managers.integrations.sftp.sftp_listener import SftpListener

# add sftpplus to the list of groups above to automate registration and named-paths group runs on file arrival at an SFTPPlus server
sftpplus.paths = from csvpath.managers.integrations.sftpplus.sftpplus_listener import SftpPlusListener

# add ckan to the list of groups above to push content and metadata to CKAN
ckan.results = from csvpath.managers.integrations.ckan.ckan_listener import CkanListener

#add marquez to the list of groups above for OpenLineage events to a Marquez server
marquez.file = from csvpath.managers.integrations.ol.file_listener_ol import OpenLineageFileListener
marquez.paths = from csvpath.managers.integrations.ol.paths_listener_ol import OpenLineagePathsListener
marquez.result = from csvpath.managers.integrations.ol.result_listener_ol import OpenLineageResultListener
marquez.results = from csvpath.managers.integrations.ol.results_listener_ol import OpenLineageResultsListener

# add slack to the list of groups above for alerts to slack webhooks
slack.file = from csvpath.managers.integrations.slack.sender import SlackSender
slack.paths = from csvpath.managers.integrations.slack.sender import SlackSender
slack.result = from csvpath.managers.integrations.slack.sender import SlackSender
slack.results = from csvpath.managers.integrations.slack.sender import SlackSender

[sqlite]
db = archive/csvpath.db

[sftp]
server = localhost
port = 22
username =
password =

[sftpplus]
# these are only needed on the server
admin_username = SFTPPLUS_ADMIN_USERNAME
admin_password = SFTPPLUS_ADMIN_PASSWORD
api_url = https://localhost:10020/json
scripts_dir =
execute_timeout = 300

# these are only needed by the csvpath writer
mailbox_user = mailbox
mailbox_password = SFTPPLUS_MAILBOX_PASSWORD
server = SFTPPLUS_SERVER
port = SFTPPLUS_PORT

[ckan]
server = http://localhost:80
api_token =

[marquez]
base_url = http://localhost:5000
endpoint = api/v1/lineage
api_key = "none"
timeout = 5
verify = False

[slack]
# add your main webhook here. to set webhooks on a csvpath-by-csvpath basis add
# on-valid-slack: webhook-minus-'https://' and/or
# on-invalid-slack: webhook-minus-'https://'
webhook_url =
            """
            file.write(c)
            print(f"Created a default config file at {directory} with name {name}.")
            print("If you want your config to be somewhere else remember to")
            print("update the path in the default config.ini")

    def _assure_logs_path(self) -> None:
        if self.load:
            filepath = self.log_file
            if not filepath or filepath.strip() == "":
                filepath = f"logs{os.sep}csvpath.log"
                self.log_file = filepath
            dirpath = self._get_dir_path(filepath)
            if dirpath and not path.exists(dirpath):
                os.makedirs(dirpath)

    def _get_dir_path(self, filepath):
        p = os.path.dirname(filepath)
        return p if not p == "" else None

    def _assure_archive_path(self) -> None:
        if self.load:
            if self.archive_path is None or self.archive_path.strip() == "":
                self.archive_path = "archive"
            if self.archive_path.strip().lower().startswith("s3://"):
                return
            if self.archive_path.strip().lower().startswith("azure://"):
                return
            if self.archive_path.strip().lower().startswith("sftp://"):
                return
            if not path.exists(self.archive_path):
                os.makedirs(self.archive_path)

    def _assure_transfer_root(self) -> None:
        if self.load:
            if self.transfer_root is None or self.transfer_root.strip() == "":
                self.transfer_root = "transfers"
            if not path.exists(self.transfer_root):
                os.makedirs(self.transfer_root)

    def _assure_inputs_files_path(self) -> None:
        if self.load:
            if self.inputs_files_path is None or self.inputs_files_path.strip() == "":
                self.inputs_files_path = f"inputs{os.sep}named_files"
            if self.inputs_files_path.strip().lower().startswith("s3://"):
                return
            if self.inputs_files_path.strip().lower().startswith("azure://"):
                return
            if self.inputs_files_path.strip().lower().startswith("sftp://"):
                return
            if self.inputs_files_path.strip().lower().startswith("gs://"):
                return
            if not path.exists(self.inputs_files_path):
                os.makedirs(self.inputs_files_path)

    def _assure_inputs_csvpaths_path(self) -> None:
        if self.load:
            if (
                self.inputs_csvpaths_path is None
                or self.inputs_csvpaths_path.strip() == ""
            ):
                self.inputs_csvpaths_path = f"inputs{os.sep}named_paths"
            if self.inputs_csvpaths_path.strip().lower().startswith("s3://"):
                return
            if self.inputs_csvpaths_path.strip().lower().startswith("azure://"):
                return
            if self.inputs_csvpaths_path.strip().lower().startswith("sftp://"):
                return
            if self.inputs_csvpaths_path.strip().lower().startswith("gs://"):
                return
            if not path.exists(self.inputs_csvpaths_path):
                os.makedirs(self.inputs_csvpaths_path)

    def _assure_cache_path(self) -> None:
        uc = self.get(section="cache", name="use_cache")
        if uc and uc.strip().lower() == "no":
            return
        if self.load:
            if self.cache_dir_path is None or self.cache_dir_path.strip() == "":
                self.cache_dir_path = "cache"
            if self.cache_dir_path.find("://") > -1:
                raise ConfigurationException(
                    f"Cache dir must be on the local drive, not {self.cache_dir_path}"
                )
            exists = path.exists(self.cache_dir_path)
            if not exists:
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
        self.refresh()

    #
    # we hold lists and such that may need refreshing from the configparser
    # object, if that has been updated or loaded. this method doesn't load from
    # file, it just gathers and translates settings for external use.
    #
    def refresh(self) -> None:
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
            if _ not in [s.value for s in OnError]:
                raise ConfigurationException(f"CsvPath error policy {_} is wrong")
        if (
            self.csvpaths_errors_policy is None
            or not isinstance(self.csvpaths_errors_policy, list)
            or not len(self.csvpaths_errors_policy) > 0
        ):
            raise ConfigurationException("CsvPaths error policy is wrong")
        for _ in self.csvpaths_errors_policy:
            if _ not in [s.value for s in OnError]:
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
        if self.csvpath_log_level not in [s.value for s in LogLevels]:
            raise ConfigurationException(f"CsvPath log level {_} is wrong")
        if self.csvpaths_log_level is None or not isinstance(
            self.csvpaths_log_level, str
        ):
            raise ConfigurationException("CsvPaths log level is wrong")
        if self.csvpaths_log_level not in [s.value for s in LogLevels]:
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

    def additional_listeners(self, listener_type) -> list[str]:
        # pull type for group names
        # for each group name find:
        #    listener_type.groupname=listner
        listeners = []
        groups = self._get("listeners", "groups")
        if groups is None:
            groups = []
        if isinstance(groups, str):
            groups = [groups]
        for group in groups:
            lst = f"{group}.{listener_type}"
            listener = self._get("listeners", lst)
            if listener is not None:
                listeners.append(listener)
        return listeners

    @property
    def cache_dir_path(self) -> str:
        return self._cache_dir_path

    @cache_dir_path.setter
    def cache_dir_path(self, p) -> None:
        self._cache_dir_path = p

    def halt_on_unmatched_file_fingerprints(self) -> bool:
        houf = self._get("inputs", "on_unmatched_file_fingerprints")
        if houf == "halt":
            return True
        elif houf == "continue":
            return False
        return None

    @property
    def transfer_root(self) -> str:
        if self._transfer_root is None:
            self._transfer_root = self._get("results", "transfers")
            if self._transfer_root is None:
                self._transfer_root = "transfers"
                self.add_to_config("results", "transfers", "transfers")
        return self._transfer_root

    @transfer_root.setter
    def transfer_root(self, p) -> None:
        self._transfer_root = p

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
    def archive_name(self) -> str:
        p = self.archive_path
        if p.find(os.sep) > -1:
            p = p[p.rfind(os.sep) + 1 :]
        return p

    @property
    def inputs_files_path(self) -> str:
        if self._inputs_files_path is None:
            self._inputs_files_path = self._get("inputs", "files")
            if self._inputs_files_path is None:
                self._inputs_files_path = "inputs"
                self.add_to_config("inputs", "files", f"inputs{os.sep}named_files")
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
                self.add_to_config("inputs", "csvpaths", f"inputs{os.sep}named_paths")
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
