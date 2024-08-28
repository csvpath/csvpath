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


class CsvPathsResultsManager(ABC):
    """this class is the manager of all the results associated with a
    CsvPaths instance. Unlike CsvPath, which are single use, a single
    CsvPaths can be used as often as needed. Results managers track all the
    results for a set of named results. Each set of named results tracks the
    output of a set of named csvpaths. Before rerunning a named set
    CsvPaths clears the named results from the ResultsManager.
    """

    @abstractmethod
    def get_variables(self, name: str) -> bool:
        pass

    @abstractmethod
    def is_valid(self, name: str) -> bool:
        pass

    @abstractmethod
    def get_number_of_results(self, name: str) -> int:
        pass

    @abstractmethod
    def set_named_results(self, results: Dict[str, List[CsvPathResult]]) -> None:
        pass

    @abstractmethod
    def add_named_result(self, name: str, result: CsvPathResult) -> None:
        pass

    @abstractmethod
    def add_named_results(self, name: str, results: List[CsvPathResult]) -> None:
        pass

    @abstractmethod
    def get_named_results(self, name: str) -> List[CsvPathResult]:
        """Named csvpaths: For each named paths, keeps and returns the most recent
        run of the paths producing results

        Named files: For each named file, keeps and returns the results of
        running any paths on the named file
        """
        pass

    @abstractmethod
    def remove_named_results(self, name: str) -> None:
        """should raise an exception if no such results"""
        pass

    @abstractmethod
    def clean_named_results(self, name: str) -> None:
        """should remove any results, completing silently if no such results"""
        pass


class ResultsManager(CsvPathsResultsManager):
    FILES_MANAGER_TYPE = "files"
    PATHS_MANAGER_TYPE = "paths"

    def __init__(self, *, csvpaths=None, type=None):
        self.named_results = dict()
        self._csvpaths = None
        self._type = None

        # use property
        self.csvpaths = csvpaths
        self.type = type

    @property
    def type(self) -> str:
        return self._type

    @type.setter
    def type(self, type: str) -> None:
        if (
            type == ResultsManager.PATHS_MANAGER_TYPE
            or type == ResultsManager.FILES_MANAGER_TYPE
        ):
            self._type = type
        else:
            raise ConfigurationException(f"type must be 'files' or 'paths', not {type}")

    @property
    def csvpaths(self) -> CsvPaths:  # noqa: F821
        return self._csvpaths

    @csvpaths.setter
    def csvpaths(self, cs: CsvPaths) -> None:  # noqa: F821
        self._csvpaths = cs

    def get_metadata(self, name: str) -> Dict[str, Any]:
        results = self.get_named_results(name)
        meta = {}
        if results and len(results):
            rs = results[0]
            path = rs.csvpath
            meta["paths name"] = rs.paths_name
            meta["file name"] = rs.file_name
            meta["lines"] = path.line_monitor.data_end_line_count
            paths = len(self.csvpaths.paths_manager.get_named_paths(name))
            meta["csvpaths applied"] = paths
            meta["csvpaths completed"] = paths == len(results)
            meta["valid"] = self.is_valid(name)
        return meta

    def is_valid(self, name: str) -> bool:
        results = self.get_named_results(name)
        for r in results:
            if not r.is_valid():
                return False
        return True

    def get_variables(self, name: str) -> bool:
        results = self.get_named_results(name)
        vs = {}
        for r in results:
            vs = {**r.csvpath.variables, **vs}
        return vs

    def get_number_of_results(self, name: str) -> int:
        nr = self.get_named_results(name)
        if nr is None:
            return 0
        else:
            return len(nr)

    def add_named_result(self, result: CsvPathResult) -> None:
        if result.file_name is None:
            raise ConfigurationException("Results must have a named-file name")
        if result.paths_name is None:
            raise ConfigurationException("Results must have a named-paths name")
        name = (
            result.file_name
            if self.type == ResultsManager.FILES_MANAGER_TYPE
            else result.paths_name
        )
        if name not in self.named_results:
            self.named_results[name] = [result]
        else:
            self.named_results[name].append(result)

    def set_named_results(self, *, results: Dict[str, List[CsvPathResult]]) -> None:
        self.named_results = results

    def add_named_results(self, name: str, results: List[CsvPathResult]) -> None:
        self.named_results[name] = results

    def remove_named_results(self, name: str) -> None:
        if name in self.named_results:
            del self.named_results[name]
        else:
            self.csvpaths.logger.warning(f"Results '{name}' not found")
            #
            # we treat this as a recoverable error because typically the user
            # has complete control of the csvpaths environment, making the
            # problem likely due to config issues that should be addressed.
            #
            # if reached by a reference this error should be trapped at an
            # expression and handled according to the error policy.
            #
            raise ConfigurationException(f"Results '{name}' not found")

    def clean_named_results(self, name: str) -> None:
        if name in self.named_results:
            self.remove_named_results(name)

    def get_named_results(self, name) -> List[List[Any]]:
        if name in self.named_results:
            return self.named_results[name]
        else:
            #
            # we treat this as a recoverable error because typically the user
            # has complete control of the csvpaths environment, making the
            # problem likely due to config issues that should be addressed.
            #
            # if reached by a reference this error should be trapped at an
            # expression and handled according to the error policy.
            #
            raise ConfigurationException(f"Results '{name}' not found")
