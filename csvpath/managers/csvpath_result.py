from __future__ import annotations
from typing import Dict, List, Any
import os
import json
from abc import ABC, abstractmethod
from .. import ConfigurationException
from .. import CsvPath, Error, Printer


class CsvPathErrorCollector(ABC):
    @abstractmethod
    def errors(self) -> List[Error]:
        pass

    @abstractmethod
    def collect_error(self, error: Error) -> None:
        pass

    @abstractmethod
    def has_errors(self) -> bool:
        pass


class CsvPathResult(CsvPathErrorCollector, Printer):
    """This class handles the results for a single CsvPath in the
    context of a CsvPaths run that may apply any number of CsvPath
    instances against the same file.
    """

    def __init__(
        self,
        *,
        lines: List[List[Any]] = None,
        csvpath: CsvPath,
        file_name: str,
        paths_name: str,
    ):
        self._lines: List[List[Any]] = None
        self._csvpath = None
        self._paths_name = paths_name
        self._file_name = file_name
        self._errors = []
        self._printouts = {}

        #
        # use the properties so error_collector, etc. is set correctly
        #
        self.csvpath = csvpath
        self.lines = lines

    @property
    def variables(self) -> Dict[str, Any]:
        return self.csvpath.variables

    @property
    def all_variables(self) -> Dict[str, Any]:
        return self.csvpath.csvpaths.results_manager.get_variables(self.paths_name)

    @property
    def paths_name(self) -> str:
        return self._paths_name

    @paths_name.setter
    def paths_name(self, paths_name: str) -> None:
        self._paths_name = paths_name

    @property
    def file_name(self) -> str:
        return self._file_name

    @file_name.setter
    def file_name(self, file_name: str) -> None:
        self._file_name = file_name

    @property
    def lines(self) -> List[List[Any]]:
        return self._lines

    @lines.setter
    def lines(self, ls: List[List[Any]]) -> None:
        self._lines = ls

    @property
    def csvpath(self) -> CsvPath:
        return self._csvpath

    @csvpath.setter
    def csvpath(self, path: CsvPath) -> None:
        path.error_collector = self
        path.add_printer(self)
        self._csvpath = path

    @property
    def errors(self) -> List[Error]:
        return self._errors

    def errors_count(self) -> int:
        return len(self._errors) if self._errors else 0

    def collect_error(self, error: Error) -> None:
        self._errors.append(error)

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def is_valid(self) -> bool:
        if self._csvpath:
            return self._csvpath.is_valid
        else:
            return False

    @property
    def printouts(self) -> List[str]:
        """this method returns the default printouts. use get_printout_by_name
        for specific printouts"""
        if self._printouts is None:
            self._printouts = []
        return self._printouts["default"] if "default" in self._printouts else []

    def get_printout_by_name(self, name: str) -> List[str]:
        if self._printouts is None:
            self._printouts = []
        return self._printous[name] if name in self._printouts else []

    def has_printouts(self) -> bool:
        return len(self._printouts) > 0 if self._printouts else False

    def print(self, string: str) -> None:
        self.print_to("default", string)

    def print_to(self, name: str, string: str) -> None:
        if name not in self._printouts:
            self._printouts[name] = []
        self._printouts[name].append(string)

    def dump_printing(self) -> None:
        for name in self._printouts:
            print(f"dumping printed lines named '{name}'")
            for line in self._printouts[name]:
                print(line)
            print("")

    def print_statements_count(self) -> int:
        i = 0
        for name in self._printouts:
            i += len(self._printouts[name]) if self._printouts[name] else 0
        return i

    def __str__(self) -> str:
        return f"""CsvPathResult
                   file:{self.csvpath.scanner.filename if self.csvpath.scanner else None};
                   name of paths:{self.paths_name};
                   name of file:{self.file_name};
                   valid:{self.csvpath.is_valid};
                   stopped:{self.csvpath.stopped};
                   last line processed:{self.csvpath.line_monitor.physical_line_number};
                   total file lines:{self.csvpath.line_monitor.physical_end_line_number};
                   matches:{self.csvpath.match_count};
                   lines captured:{len(self.lines) if self.lines else 0};
                   print statements:{self.print_statements_count()};
                   errors:{len(self.errors)}"""
