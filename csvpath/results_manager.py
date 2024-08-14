from typing import Dict, List, Any
import os
import json
from abc import ABC, abstractmethod
from . import ConfigurationException
from . import CsvPath


class CsvPathResult:
    def __init__(self, *, lines: List[List[Any]] = None, path: CsvPath = None):
        self.lines: List[List[Any]] = lines
        self.path = path

    def is_valid(self) -> bool:
        if self.path:
            return self.path.is_valid
        else:
            return False


class CsvPathsResultsManager(ABC):
    @abstractmethod
    def get_variables(self, name: str) -> bool:
        pass

    @abstractmethod
    def is_valid(self, name: str) -> bool:
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
    def __init__(self, *, named_results: Dict[str, List[CsvPathResult]] = {}):
        self.named_results = named_results

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
            vs += r.path.variables
        return vs

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
