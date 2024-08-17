from typing import Dict, List, Any
import os
import json
from abc import ABC, abstractmethod
from .. import ConfigurationException
from .. import CsvPath, Error


class CsvPathResult:
    def __init__(self, *, lines: List[List[Any]] = None, path: CsvPath = None):
        self._lines: List[List[Any]] = lines
        self._csvpath = path
        self._errors = []

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
        self._csvpath = path

    @property
    def errors(self) -> List[Error]:
        return self._errors

    def collect_error(self, err: Error) -> None:
        self._errors.append(err)

    def is_valid(self) -> bool:
        if self._csvpath:
            return self._csvpath.is_valid
        else:
            return False

    def __str__(self) -> str:
        return f"""CsvPathResult:
                        valid:{self.csvpath.is_valid};
                        path:{self.csvpath};
                        lines:{len(self.lines) if self.lines else None};
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
