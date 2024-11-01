# pylint: disable=C0114
from __future__ import annotations
from typing import Dict, List, Any
from abc import ABC, abstractmethod
from .result import Result
from ..util.exceptions import InputException


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
        """gets all the variables from all csvpaths in one dict. variables may
        overwrite each other"""

    @abstractmethod
    def is_valid(self, name: str) -> bool:
        """True if all csvpaths are valid"""

    @abstractmethod
    def has_lines(self, name: str) -> bool:
        """True if lines were captured by any of the csvpaths under name"""

    @abstractmethod
    def has_errors(self, name: str) -> bool:
        """True if the error collectors for any of the csvpaths under name
        have any errors"""

    @abstractmethod
    def get_number_of_errors(
        self, name: str
    ) -> bool:  # pylint: disable=C0116  pragma: no cover
        pass

    @abstractmethod
    def get_number_of_results(
        self, name: str
    ) -> int:  # pylint: disable=C0116   pragma: no cover
        pass

    @abstractmethod
    def set_named_results(self, results: Dict[str, List[Result]]) -> None:
        """overwrite"""

    @abstractmethod
    def add_named_result(self, result: Result) -> None:
        """additive. the results are named in the result object."""

    @abstractmethod
    def add_named_results(self, results: List[Result]) -> None:
        """additive. the results are named in the result object."""

    @abstractmethod
    def get_named_results(self, name: str) -> List[Result]:
        """For each named-paths, keeps and returns the most recent
        run of the paths producing results
        """

    @abstractmethod
    def get_specific_named_result(self, name: str, name_or_id: str) -> Result:
        """Finds a result with a metadata field named id or name that has a
        value matching name_or_id. id is wins over name. first results with either
        wins. the name or id comes from a comment's metadata field that would look
        like ~ id: my_path ~ or ~ name: my_path ~
        The allowable forms of id or name are all lower, all upper or initial case.
        i.e.: id, ID, Id and name, NAME, Name.
        """

    @abstractmethod
    def remove_named_results(self, name: str) -> None:
        """should raise an exception if no such results"""

    @abstractmethod
    def clean_named_results(self, name: str) -> None:
        """should remove any results, completing silently if no such results"""


class ResultsManager(CsvPathsResultsManager):  # pylint: disable=C0115
    FILES_MANAGER_TYPE = "files"
    PATHS_MANAGER_TYPE = "paths"

    def __init__(self, *, csvpaths=None):
        self.named_results = {}
        self._csvpaths = None

        # use property
        self.csvpaths = csvpaths

    @property
    def csvpaths(self):  # noqa: F821 pylint: disable=C0116
        return self._csvpaths

    @csvpaths.setter
    def csvpaths(self, cs) -> None:  # noqa: F821
        self._csvpaths = cs

    def get_metadata(self, name: str) -> Dict[str, Any]:
        """gets the run metadata. will include the metadata complete from
        the first results. however, the metadata for individual results must
        come direct from them in order to not overwrite"""
        results = self.get_named_results(name)
        meta = {}
        if results and len(results) > 0:
            rs = results[0]
            path = rs.csvpath
            meta["paths_name"] = rs.paths_name
            meta["file_name"] = rs.file_name
            meta["data_lines"] = path.line_monitor.data_end_line_count
            paths = len(self.csvpaths.paths_manager.get_named_paths(name))
            meta["csvpaths_applied"] = paths
            meta["csvpaths_completed"] = paths == len(results)
            meta["valid"] = self.is_valid(name)
            meta = {**meta, **rs.csvpath.metadata}
        return meta

    def get_specific_named_result(self, name: str, name_or_id: str) -> Result:
        results = self.get_named_results(name)
        if results and len(results) > 0:
            for r in results:
                if name_or_id == r.csvpath.identity:
                    return r
        return None  # pragma: no cover

    def is_valid(self, name: str) -> bool:
        results = self.get_named_results(name)
        for r in results:
            if not r.is_valid:
                return False
        return True

    def get_variables(self, name: str) -> bool:
        results = self.get_named_results(name)
        vs = {}
        for r in results:
            vs = {**r.csvpath.variables, **vs}
        return vs

    def has_lines(self, name: str) -> bool:
        results = self.get_named_results(name)
        for r in results:
            if r.lines and len(r.lines) > 0:
                return True
        return False

    def get_number_of_results(self, name: str) -> int:
        nr = self.get_named_results(name)
        if nr is None:
            return 0
        return len(nr)

    def has_errors(self, name: str) -> bool:
        results = self.get_named_results(name)
        for r in results:
            if r.has_errors():
                return True
        return False

    def get_number_of_errors(self, name: str) -> bool:
        results = self.get_named_results(name)
        errors = 0
        for r in results:
            errors += r.errors_count()
        return errors

    def add_named_result(self, result: Result) -> None:
        if result.file_name is None:
            raise InputException("Results must have a named-file name")
        if result.paths_name is None:
            raise InputException("Results must have a named-paths name")
        name = result.paths_name
        if name not in self.named_results:
            self.named_results[name] = [result]
        else:
            self.named_results[name].append(result)
        self._variables = None

    def set_named_results(self, results: Dict[str, List[Result]]) -> None:
        self.named_results = {}
        # for key, value in results.items():
        for value in results.values():
            self.add_named_results(value)

    def add_named_results(self, results: List[Result]) -> None:
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
            # problem config that should be addressed.
            #
            # if reached by a reference this error should be trapped at an
            # expression and handled according to the error policy.
            #
            raise InputException(f"Results '{name}' not found")

    def clean_named_results(self, name: str) -> None:
        if name in self.named_results:
            self.remove_named_results(name)

    def get_named_results(self, name) -> List[List[Any]]:
        if name in self.named_results:
            return self.named_results[name]
        #
        # we treat this as a recoverable error because typically the user
        # has complete control of the csvpaths environment, making the
        # problem config that should be addressed.
        #
        # if reached by a reference this error should be trapped at an
        # expression and handled according to the error policy.
        #
        raise InputException(f"Results '{name}' not found")
