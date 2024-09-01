from __future__ import annotations
from typing import Dict, List, Any
import os
import json
from abc import ABC, abstractmethod
from .. import ConfigurationException
from .. import CsvPath, Error, CsvPathResult


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

    def __init__(self, *, csvpaths=None):
        self.named_results = dict()
        self._csvpaths = None
        self._variables = None

        # use property
        self.csvpaths = csvpaths

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
            meta["paths_name"] = rs.paths_name
            meta["file_name"] = rs.file_name
            meta["data_lines"] = path.line_monitor.data_end_line_count
            paths = len(self.csvpaths.paths_manager.get_named_paths(name))
            meta["csvpaths_applied"] = paths
            meta["csvpaths_completed"] = paths == len(results)
            meta["valid"] = self.is_valid(name)
            meta["all_variables"] = self.get_variables(name)
            meta = {**meta, **rs.csvpath.metadata}
        return meta

    def is_valid(self, name: str) -> bool:
        results = self.get_named_results(name)
        for r in results:
            if not r.is_valid():
                return False
        return True

    def get_variables(self, name: str) -> bool:
        if self._variables is None:
            results = self.get_named_results(name)
            vs = {}
            for r in results:
                vs = {**r.csvpath.variables, **vs}
            self._variables = vs
        return self._variables

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
        name = result.paths_name
        if name not in self.named_results:
            self.named_results[name] = [result]
        else:
            self.named_results[name].append(result)
        self._variables = None

    def set_named_results(self, *, results: Dict[str, List[CsvPathResult]]) -> None:
        self.named_results = {}
        for key, value in results.items():
            self.add_named_results(key, value)

    def add_named_results(self, name: str, results: List[CsvPathResult]) -> None:
        for r in results:
            self.add_named_result(r)

    def remove_named_results(self, name: str) -> None:
        if name in self.named_results:
            del self.named_results[name]
            self._variables = None
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
