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
    def __init__(self, *, lines: List[List[Any]] = None, path: CsvPath = None):
        self._lines: List[List[Any]] = None
        self._csvpath = None
        self._name = None
        self._errors = []
        self._results_index = -1
        self._printouts = {}
        #
        # use the properties so error_collector, etc. is set correctly
        #
        self.csvpath = path
        self.lines = lines

    @property
    def results_index(self) -> int:
        return self._results_index

    @results_index.setter
    def results_index(self, index: int) -> None:
        self._results_index = index

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        self._name = name

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
        """this method returns the default printouts. use get_printout_by_name for specific printouts"""
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
                   name of csvpaths:{self.name};
                   results index:{self.results_index};
                   valid:{self.csvpath.is_valid};
                   stopped:{self.csvpath.stopped};
                   last line processed:{self.csvpath.line_number};
                   total file lines:{self.csvpath.total_lines};
                   matches:{self.csvpath.match_count};
                   lines captured:{len(self.lines) if self.lines else 0};
                   print statements:{self.print_statements_count()};
                   errors:{len(self.errors)}"""


class CsvPathsResultsManager(ABC):
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
        pass

    @abstractmethod
    def remove_named_results(self, name: str) -> None:
        pass


class ResultsManager(CsvPathsResultsManager):
    def __init__(self):
        self.named_results = dict()

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

    def add_named_result(self, name: str, result: CsvPathResult) -> None:
        result.name = name
        result.results_index = len(self.named_results)
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
            raise ConfigurationException(f"Results {name} not found")

    def get_named_results(self, name) -> List[List[Any]]:
        if name in self.named_results:
            return self.named_results[name]
        else:
            raise ConfigurationException(f"Results {name} not found")
