from typing import Dict, List, Any
import csv
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
        """gets a CsvPath object primed with a reference to this CsvPaths"""
        pass

    @abstractmethod
    def collect_paths(self, pathsname, filename) -> None:
        """sequentially does a CsvPath.collect() on filename for every named path"""
        pass

    @abstractmethod
    def fast_forward_paths(self, pathsname, filename) -> None:
        """sequentially does a CsvPath.fast_forward() on filename for every named path"""
        pass

    @abstractmethod
    def next_paths(self, pathsname, filename) -> None:
        """does a CsvPath.next() on filename for every line against every named path in sequence"""
        pass

    @abstractmethod
    def collect_by_line(self, pathsname, filename):
        """does a CsvPath.collect() on filename where each row is considered by every named path before the next row starts"""
        pass

    @abstractmethod
    def fast_forward_by_line(self, pathsname, filename):
        """does a CsvPath.fast_forward() on filename where each row is considered by every named path before the next row starts"""
        pass

    @abstractmethod
    def next_by_line(self, pathsname, filename, collect: bool = False) -> List[Any]:
        """does a CsvPath.next() on filename where each row is considered by every named path before the next row starts"""
        pass


class CsvPaths(CsvPathsCenter):
    def __init__(self, *, delimiter=",", quotechar='"', skip_blank_lines=True):
        self.paths_manager = PathsManager()
        self.files_manager = FilesManager()
        self.results_manager = ResultsManager()

        self.delimiter = delimiter
        self.quotechar = quotechar
        self.skip_blank_lines = skip_blank_lines
        self.current_matchers: List[CsvPath] = []

    def csvpath(self) -> CsvPath:
        return CsvPath(
            csvpaths=self,
            delimiter=self.delimiter,
            quotechar=self.quotechar,
            skip_blank_lines=self.skip_blank_lines,
        )

    def collect_paths(self, pathsname, filename) -> None:
        if pathsname not in self.paths_manager.named_paths:
            raise ConfigurationException("pathsname must be a named set of paths")
        if filename not in self.files_manager.named_files:
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
        if pathsname not in self.paths_manager.named_paths:
            raise ConfigurationException("pathsname must be a named set of paths")
        if filename not in self.files_manager.named_files:
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

    def next_paths(self, pathsname, filename):
        if pathsname not in self.paths_manager.named_paths:
            raise ConfigurationException(
                f"pathsname '{pathsname}' must be a named set of paths"
            )
        if filename not in self.files_manager.named_files:
            raise ConfigurationException(f"filename '{filename}' must be a named file")
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

    # =============== breadth first processing ================

    def collect_by_line(self, pathsname, filename):
        for line in self.process_by_line(
            pathsname=pathsname, filename=filename, collect=True
        ):
            pass

    def fast_forward_by_line(self, pathsname, filename):
        for line in self.process_by_line(
            pathsname=pathsname, filename=filename, collect=False
        ):
            pass

    def next_by_line(self, pathsname, filename, collect: bool = False) -> List[Any]:
        if filename not in self.files_manager.named_files:
            raise ConfigurationException(f"filename '{filename}' must be a named file")
        fn = self.files_manager.get_named_file(filename)
        if not fn:
            raise ConfigurationException(f"filename '{filename}' must be a named file")
        if pathsname not in self.paths_manager.named_paths:
            raise ConfigurationException(
                f"pathsname '{pathsname}' must name a set of csvpaths"
            )
        paths = self.paths_manager.get_named_paths(pathsname)
        if not isinstance(paths, list) or len(paths) == 0:
            raise ConfigurationException(
                f"pathsname '{pathsname}' must name a list of csvpaths"
            )

        csvpath_objects = []
        for path in paths:
            csvpath = self.csvpath()
            f = path.find("[")
            path = f"${fn}{path[f:]}"
            csvpath.parse(path)
            csvpath_objects.append((csvpath, []))
        #
        # setting fn into the csvpath is less obviously useful at CsvPaths
        # but we'll do it for consistency.
        #
        with open(fn, "r") as file:
            reader = csv.reader(
                file, delimiter=self.delimiter, quotechar=self.quotechar
            )
            stopped_count: List[int] = []
            for line in reader:
                self.current_matchers: List[CsvPath] = []
                for p in csvpath_objects:
                    if p[0].stopped:
                        stopped_count.append(1)
                    else:
                        b = p[0]._consider_line(line)
                        if b and collect:
                            p[1].append(line)
                        if b:
                            self.current_matchers.append(p[0])
                            # yield line
                if len(self.current_matchers) > 0:
                    yield line
                if sum(stopped_count) == len(csvpath_objects):
                    break
        for csvpath in csvpath_objects:
            result = CsvPathResult(path=csvpath[0], lines=csvpath[1])
            self.results_manager.add_named_result(pathsname, result)
