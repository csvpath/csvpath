# pylint: disable=C0114
import os
import json
from json import JSONDecodeError
from typing import Dict, List
from abc import ABC, abstractmethod
from ..util.line_counter import LineCounter
from ..util.line_monitor import LineMonitor
from ..util.error import ErrorHandler


class CsvPathsFilesManager(ABC):
    """files managers map fully qualified or relative file paths to
    simple names to make it easier to trigger csvpath runs. unlike
    paths and results manager, files managers are mostly a
    convenience."""

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
        pass

    @abstractmethod
    def remove_named_file(self, name: str) -> None:  # pylint: disable=C0116
        pass

    @abstractmethod
    def get_new_line_monitor(self, filename: str) -> LineMonitor:
        pass

    @abstractmethod
    def get_original_headers(self, filename: str) -> List[str]:
        pass


class FilesManager(CsvPathsFilesManager):  # pylint: disable=C0115
    def __init__(self, *, named_files: Dict[str, str] = None, csvpaths):
        if named_files is None:
            named_files = {}
        self.named_files: Dict[str, str] = named_files
        self.csvpaths = csvpaths
        self.pathed_lines_and_headers = {}

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
        lc = LineCounter(self.csvpaths)
        lm, headers = lc.get_lines_and_headers(filename)
        self.pathed_lines_and_headers[filename] = (lm, headers)

    def set_named_files(self, nf: Dict[str, str]) -> None:
        self.named_files = nf

    def set_named_files_from_json(self, filename: str) -> None:
        try:
            with open(filename, encoding="utf-8") as f:
                j = json.load(f)
                self.named_files = j
        except (OSError, ValueError, TypeError, JSONDecodeError) as ex:
            ErrorHandler(self.csvpaths).handle_error(ex)

    def add_named_files_from_dir(self, dirname: str):
        dlist = os.listdir(dirname)
        base = dirname
        for p in dlist:
            _ = p.lower()
            ext = p[p.rfind(".") + 1 :].strip().lower()
            if ext in self.csvpaths.config.csv_file_extensions:
                name = self._name_from_name_part(p)
                path = os.path.join(base, p)
                self.named_files[name] = path
            else:
                self.csvpaths.logger.debug(
                    "Skipping %s because extension not in accept list",
                    os.path.join(base, p),
                )

    def add_named_file(self, *, name: str, path: str) -> None:
        self.named_files[name] = path

    def get_named_file(self, name: str) -> str:
        if name not in self.named_files:
            return None
        return self.named_files[name]

    def remove_named_file(self, name: str) -> None:
        if name in self.named_files:
            del self.named_files[name]

    def _name_from_name_part(self, name):
        i = name.rfind(".")
        if i == -1:
            pass
        else:
            name = name[0:i]
        return name
