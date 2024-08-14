from typing import Dict, List, Any
import os
import json
from . import CsvPath
from . import FileException
from . import ConfigurationException
from . import PathsManager
from . import FilesManager
from . import ResultsManager, CsvPathResult
from abc import ABC, abstractmethod


class CsvPathsCenter(ABC):
    @abstractmethod
    def csvpath(self) -> CsvPath:
        pass

    @abstractmethod
    def collect_paths(self, pathsname, filename):
        pass

    @abstractmethod
    def fast_forward_paths(self, pathsname, filename):
        pass

    @abstractmethod
    def next(self, pathsname, filename):
        pass


class CsvPaths(CsvPathsCenter):
    def __init__(
        self,
        *,
        delimiter=",",
        quotechar='"',
        skip_blank_lines=True,
    ):
        self.paths_manager = PathsManager()
        self.files_manager = FilesManager()
        self.results_manager = ResultsManager()

        self.delimiter = delimiter
        self.quotechar = quotechar
        self.skip_blank_lines = skip_blank_lines

    def csvpath(self) -> CsvPath:
        return CsvPath(
            csvpaths=self,
            delimiter=self.delimiter,
            quotechar=self.quotechar,
            skip_blank_lines=self.skip_blank_lines,
        )

    def collect_paths(self, pathsname, filename):
        if pathsname not in self.named_paths:
            raise ConfigurationException("pathsname must be a named set of paths")
        if filename not in self.named_files:
            raise ConfigurationException("filename must be a named file")
        paths = self.paths_manager.get_named_paths(pathsname)
        file = self.files_manager.get_named_file(filename)
        for path in paths:
            csvpath = self.csvpath()
            f = path.find("[")
            path = f"${file}{path[f:]}"
            csvpath.parse(path)
            lines = csvpath.collect()
            result = CsvPathResult(path=csvpath, lines=lines)
            self.results_manager.add_named_result(pathsname, result)

    def fast_forward_paths(self, pathsname, filename):
        if pathsname not in self.named_paths:
            raise ConfigurationException("pathsname must be a named set of paths")
        if filename not in self.named_files:
            raise ConfigurationException("filename must be a named file")
        paths = self.paths_manager.get_named_paths(pathsname)
        file = self.files_manager.get_named_file(filename)
        for path in paths:
            csvpath = self.csvpath()
            f = path.find("[")
            path = f"${file}{path[f:]}"
            csvpath.parse(path)
            csvpath.fast_forward()
            result = CsvPathResult(path=csvpath, lines=None)
            self.results_manager.add_named_result(pathsname, result)

    def next(self, pathsname, filename):
        if pathsname not in self.named_paths:
            raise ConfigurationException("pathsname must be a named set of paths")
        if filename not in self.named_files:
            raise ConfigurationException("filename must be a named file")
        paths = self.paths_manager.get_named_paths(pathsname)
        file = self.files_manager.get_named_file(filename)
        for path in paths:
            csvpath = self.csvpath()
            f = path.find("[")
            path = f"${file}{path[f:]}"
            csvpath.parse(path)
            for line in csvpath.next():
                yield line
            result = CsvPathResult(path=csvpath, lines=None)
            self.results_manager.add_named_result(pathsname, result)
