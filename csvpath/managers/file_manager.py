# pylint: disable=C0114
import os
import json
import csv
import hashlib
import shutil
from abc import ABC, abstractmethod
from json import JSONDecodeError
from typing import Dict, List, Tuple
from ..util.line_counter import LineCounter
from ..util.line_monitor import LineMonitor
from ..util.error import ErrorHandler
from ..util.cache import Cache
from ..util.file_readers import DataFileReader
from ..util.reference_parser import ReferenceParser
from ..util.exceptions import InputException
from .file_registrar import FileRegistrar


class CsvPathsFileManager(ABC):
    """file managers map fully qualified or relative file paths to
    simple names to make it easier to trigger csvpath runs.
    """

    @abstractmethod
    def add_named_files_from_dir(self, dirname: str) -> None:
        """each file is named by its simple name, minus extension.
        files are added so you can add multiple directories."""

    @abstractmethod
    def set_named_files_from_json(self, filename: str) -> None:
        """files are keyed by their simple name, minus extension,
        in a dict. the files are set so each time you do this you overwrite"""

    @abstractmethod
    def set_named_files(self, nf: Dict[str, str]) -> None:
        """overwrite"""

    @abstractmethod
    def add_named_file(self, *, name: str, path: str) -> None:
        """additive"""

    @abstractmethod
    def get_named_file(self, name: str) -> str:  # pylint: disable=C0116
        """gets the file system path for the nickname"""

    @abstractmethod
    def remove_named_file(self, name: str) -> None:  # pylint: disable=C0116
        """removes the named-file by its nickname"""

    @abstractmethod
    def get_new_line_monitor(self, filename: str) -> LineMonitor:
        """gets a new LineMonitor prepopulated with cached counts"""

    @abstractmethod
    def get_original_headers(self, filename: str) -> List[str]:
        """gets the cached headers"""

    @property
    @abstractmethod
    def named_files_count(self) -> int:
        pass

    @property
    @abstractmethod
    def named_file_names(self) -> list:
        pass


class FileManager(CsvPathsFileManager):  # pylint: disable=C0115
    def __init__(self, *, named_files: Dict[str, str] = None, csvpaths=None):
        if named_files is None:
            named_files = {}
        # self.named_files: Dict[str, str] = named_files
        self.csvpaths = csvpaths
        self.pathed_lines_and_headers = {}
        self.cache = Cache(self.csvpaths)
        self._registrar = FileRegistrar(self.csvpaths.config)

    @property
    def registrar(self) -> FileRegistrar:
        return self._registrar

    def get_new_line_monitor(self, filename: str) -> LineMonitor:
        if filename not in self.pathed_lines_and_headers:
            self._find_lines_and_headers(filename)
        lm = self.pathed_lines_and_headers[filename][0]
        lm = lm.copy()
        return lm

    def get_original_headers(self, filename: str) -> List[str]:
        if filename not in self.pathed_lines_and_headers:
            self._find_lines_and_headers(filename)
        return self.pathed_lines_and_headers[filename][1][:]

    def _find_lines_and_headers(self, filename: str) -> None:
        lm, headers = self._cached_lines_and_headers(filename)
        if lm is None or headers is None:
            lc = LineCounter(self.csvpaths)
            lm, headers = lc.get_lines_and_headers(filename)
            self._cache_lines_and_headers(filename, lm, headers)
        self.pathed_lines_and_headers[filename] = (lm, headers)

    # ========================================
    # cache related
    #

    def _cached_lines_and_headers(self, filename: str) -> Tuple[LineMonitor, List[str]]:
        lm = LineMonitor()
        json = self.cache.cached_text(filename, "json")
        if json is not None and not json.strip() == "":
            lm.load(json)
        else:
            return (None, None)
        headers = self.cache.cached_text(filename, "csv")
        return (lm, headers)

    def _cache_lines_and_headers(
        self, filename, lm: LineMonitor, headers: List[str]
    ) -> None:
        jstr = lm.dump()
        self.cache.cache_text(filename, "json", jstr)
        self.cache.cache_text(filename, "csv", ",".join(headers))

    #
    # ========================================

    @property
    def named_files_count(self) -> int:
        return len(self.named_file_names)

    @property
    def named_file_names(self) -> list:
        b = self.registrar.named_files_dir
        ns = [n for n in os.listdir(b) if not os.path.isfile(os.path.join(b, n))]
        return ns

    def name_exists(self, name) -> bool:
        return self.registrar.name_exists(name)

    def remove_named_file(self, name: str) -> None:
        p = os.path.join(self.registrar.named_files_dir, name)
        shutil.rmtree(p)

    def remove_all_named_files(self) -> None:
        names = self.named_file_names
        for name in names:
            self.remove_named_file(name)

    def set_named_files(self, nf: Dict[str, str]) -> None:
        for k, v in nf.items():
            self.add_named_file(name=k, path=v)

    def set_named_files_from_json(self, filename: str) -> None:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                j = json.load(f)
                self.set_named_files(j)
        except (OSError, ValueError, TypeError, JSONDecodeError) as ex:
            ErrorHandler(csvpaths=self.csvpaths).handle_error(ex)

    def add_named_files_from_dir(self, dirname: str):
        dlist = os.listdir(dirname)
        base = dirname
        for p in dlist:
            _ = p.lower()
            ext = p[p.rfind(".") + 1 :].strip().lower()
            if ext in self.csvpaths.config.csv_file_extensions:
                name = self._name_from_name_part(p)
                path = os.path.join(base, p)
                self.add_named_file(name=name, path=path)
            else:
                self.csvpaths.logger.debug(
                    "Skipping %s because extension not in accept list",
                    os.path.join(base, p),
                )

    def add_named_file(self, *, name: str, path: str) -> None:
        #
        # why are we using a new registrar rather than the one held by
        # this instance? holdover?
        #
        reg = FileRegistrar(self.csvpaths.config)
        reg.register_named_file(name=name, path=path)

    #
    # can take a reference. the ref would only be expected to point
    # to the results of a csvpath in a named-paths group. it would be
    # in this form: $group.results.2024-01-01_10-15-20.mypath
    # where this gets interesting is the datestamp identifing the
    # run. we need to allow for var sub and/or other shortcuts
    #
    def get_named_file(self, name: str) -> str:
        ret = None
        if name.startswith("$"):
            ref = ReferenceParser(name)
            if ref.datatype != ReferenceParser.RESULTS:
                raise InputException(
                    f"Reference datatype must be {ReferenceParser.RESULTS}"
                )
            reman = self.csvpaths.results_manager
            ret = reman.data_file_for_reference(name)
        else:
            reg = self.registrar
            ret = reg.registered_file(name)
        return ret

    def get_named_file_reader(self, name: str) -> DataFileReader:
        path = self.get_named_file(name)
        t = self.registrar.type_of_file(name)
        return FileManager.get_reader(path, filetype=t)

    @classmethod
    def get_reader(
        cls, path: str, *, filetype: str = None, delimiter=None, quotechar=None
    ) -> DataFileReader:
        return DataFileReader(
            path, filetype=filetype, delimiter=delimiter, quotechar=quotechar
        )

    def _name_from_name_part(self, name):
        i = name.rfind(".")
        if i == -1:
            pass
        else:
            name = name[0:i]
        return name
