from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple
import csv
import os
import json
import traceback
from csvpath.util.error import ErrorHandler
from csvpath.util.config import CsvPathConfig
from . import CsvPath
from . import FileException
from . import ConfigurationException
from . import PathsManager
from . import FilesManager
from . import ResultsManager, CsvPathResult


class CsvPathsPublic(ABC):
    """A CsvPaths instance manages appying any number of csvpaths
    to any number of files. CsvPaths applies sets of csvpaths
    to a given file, on demand. Think of CsvPaths as a session
    object. It gives you a way to manage files, csvpaths, and
    the results generated by applying paths to files. It is not
    intended for concurrent use. If you need multiple threads,
    create multiple CsvPaths instances.
    """

    @abstractmethod
    def csvpath(self) -> CsvPath:  # pragma: no cover
        """Gets a CsvPath object primed with a reference to this CsvPaths"""
        pass

    @abstractmethod
    def collect_paths(self, pathsname, filename) -> None:  # pragma: no cover
        """Sequentially does a CsvPath.collect() on filename for every named path"""
        pass

    @abstractmethod
    def fast_forward_paths(self, pathsname, filename) -> None:  # pragma: no cover
        """Sequentially does a CsvPath.fast_forward() on filename for every named path"""
        pass

    @abstractmethod
    def next_paths(self, pathsname, filename) -> None:  # pragma: no cover
        """Does a CsvPath.next() on filename for every line against every named path in sequence"""
        pass

    @abstractmethod
    def collect_by_line(self, pathsname, filename):  # pragma: no cover
        """Does a CsvPath.collect() on filename where each row is considered by every named path before the next row starts"""
        pass

    @abstractmethod
    def fast_forward_by_line(self, pathsname, filename):  # pragma: no cover
        """Does a CsvPath.fast_forward() on filename where each row is considered by every named path before the next row starts"""
        pass

    @abstractmethod
    def next_by_line(
        self, pathsname, filename, collect: bool = False
    ) -> List[Any]:  # pragma: no cover
        """Does a CsvPath.next() on filename where each row is considered by every named path before the next row starts"""
        pass


class CsvPaths(CsvPathsPublic):
    """Manages the application of csvpaths to files. Csvpaths must be grouped and named.
    Files must be named. Results are indexed by `path_results_manager` and
    `file_results_manager`. CsvPaths instances can be reused. Path results and
    file results can be out of sync, which may be useful at times.
    """

    def __init__(
        self, *, delimiter=",", quotechar='"', skip_blank_lines=True, print_default=True
    ):
        self.paths_manager = PathsManager(csvpaths=self)
        self.files_manager = FilesManager(csvpaths=self)
        self.path_results_manager = ResultsManager(csvpaths=self, type="paths")
        self.file_results_manager = ResultsManager(csvpaths=self, type="files")
        self.print_default = print_default
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.skip_blank_lines = skip_blank_lines
        self.current_matchers: List[CsvPath] = []
        self.config = CsvPathConfig()
        self.logger = self.config.get_logger("csvpaths")
        self.logger.info("initialized CsvPaths")
        self._error_collector = None

    def csvpath(self) -> CsvPath:
        return CsvPath(
            csvpaths=self,
            delimiter=self.delimiter,
            quotechar=self.quotechar,
            skip_blank_lines=self.skip_blank_lines,
            config=self.config,
            print_default=self.print_default,
        )

    def collect_paths(self, *, pathsname, filename) -> None:
        if pathsname not in self.paths_manager.named_paths:
            raise ConfigurationException("pathsname must be a named set of paths")
        if filename not in self.files_manager.named_files:
            raise ConfigurationException("filename must be a named file")
        paths = self.paths_manager.get_named_paths(pathsname)
        file = self.files_manager.get_named_file(filename)
        self.logger.info(f"beginning collect_paths with {len(paths)} paths")
        for path in paths:
            try:
                csvpath = self.csvpath()
                result = CsvPathResult(
                    csvpath=csvpath, file_name=filename, paths_name=pathsname
                )
                self.path_results_manager.add_named_result(result)
                self.file_results_manager.add_named_result(result)
                f = path.find("[")
                path = f"${file}{path[f:]}"
                csvpath.parse(path)
                lines = csvpath.collect()
                result.lines = lines
            except Exception as ex:
                ex.trace = traceback.format_exc()
                ex.source = self
                ErrorHandler(csvpaths=self).handle_error(ex)

    def fast_forward_paths(self, *, pathsname, filename):
        if pathsname not in self.paths_manager.named_paths:
            raise ConfigurationException("pathsname must be a named set of paths")
        if filename not in self.files_manager.named_files:
            raise ConfigurationException("filename must be a named file")
        paths = self.paths_manager.get_named_paths(pathsname)
        file = self.files_manager.get_named_file(filename)
        self.logger.info(f"beginning fast_forward_paths with {len(paths)} paths")
        for path in paths:
            try:
                csvpath = self.csvpath()
                result = CsvPathResult(
                    csvpath=csvpath, file_name=filename, paths_name=pathsname
                )
                self.path_results_manager.add_named_result(result)
                self.file_results_manager.add_named_result(result)
                f = path.find("[")
                apath = f"${file}{path[f:]}"
                csvpath.parse(apath)
                csvpath.fast_forward()
            except Exception as ex:
                ex.trace = traceback.format_exc()
                ex.source = self
                ErrorHandler(csvpaths=self).handle_error(ex)

    def next_paths(self, *, pathsname, filename):
        """appends the CsvPathResult for each CsvPath to the end of
        each line it produces. this is so that the caller can easily
        interrogate the CsvPath for its path parts, file, etc."""
        if pathsname not in self.paths_manager.named_paths:
            raise ConfigurationException(
                f"pathsname '{pathsname}' must be a named set of paths"
            )
        if filename not in self.files_manager.named_files:
            raise ConfigurationException(f"filename '{filename}' must be a named file")
        paths = self.paths_manager.get_named_paths(pathsname)
        file = self.files_manager.get_named_file(filename)
        self.logger.info(f"beginning next_paths with {len(paths)} paths")
        for path in paths:
            try:
                csvpath = self.csvpath()
                result = CsvPathResult(
                    csvpath=csvpath, file_name=filename, paths_name=pathsname
                )
                self.path_results_manager.add_named_result(result)
                self.file_results_manager.add_named_result(result)
                f = path.find("[")
                path = f"${file}{path[f:]}"
                csvpath.parse(path)
                for line in csvpath.next():
                    line.append(result)
                    yield line
            except Exception as ex:
                ex.trace = traceback.format_exc()
                ex.source = self
                ErrorHandler(csvpaths=self).handle_error(ex)

    # =============== breadth first processing ================

    def collect_by_line(self, *, pathsname, filename):
        for line in self.next_by_line(
            pathsname=pathsname, filename=filename, collect=True
        ):
            pass

    def fast_forward_by_line(self, *, pathsname, filename):
        for line in self.next_by_line(
            pathsname=pathsname, filename=filename, collect=False
        ):
            pass

    def next_by_line(self, *, pathsname, filename, collect: bool = False) -> List[Any]:
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

        csvpath_objects = self._load_csvpath_objects(paths=paths, named_file=fn)
        self._prep_csvpath_results(
            csvpath_objects=csvpath_objects, filename=filename, pathsname=pathsname
        )
        #
        # setting fn into the csvpath is less obviously useful at CsvPaths
        # but we'll do it for consistency.
        #
        self.logger.info(f"beginning next_by_line with {len(csvpath_objects)} paths")
        with open(fn, "r") as file:
            reader = csv.reader(
                file, delimiter=self.delimiter, quotechar=self.quotechar
            )
            stopped_count: List[int] = []
            for line in reader:
                try:
                    self.current_matchers: List[CsvPath] = []
                    for p in csvpath_objects:
                        if p[0].stopped:
                            stopped_count.append(1)
                        else:
                            b = p[0]._consider_line(line)
                            p[0].line_number = p[0].line_number + 1
                            if b and collect:
                                line = p[0].limit_collection(line)
                                p[1].append(line)
                            if b:
                                self.current_matchers.append(p[0])
                                # yield line
                    if len(self.current_matchers) > 0:
                        yield line
                    if sum(stopped_count) == len(csvpath_objects):
                        break
                except Exception as ex:
                    ex.trace = traceback.format_exc()
                    ex.source = self
                    ErrorHandler(csvpaths=self).handle_error(ex)

    def _load_csvpath_objects(
        self, *, paths: List[str], named_file: str
    ) -> List[Tuple[CsvPath, List]]:
        csvpath_objects = []
        for path in paths:
            try:
                csvpath = self.csvpath()
                f = path.find("[")
                path = f"${named_file}{path[f:]}"
                csvpath.parse(path)
                csvpath_objects.append((csvpath, []))
            except Exception as ex:
                ex.trace = traceback.format_exc()
                ex.source = self
                ErrorHandler(csvpaths=self).handle_error(ex)
        return csvpath_objects

    def _prep_csvpath_results(self, *, csvpath_objects, filename, pathsname):
        for csvpath in csvpath_objects:
            try:
                #
                # lines object is a shared reference between path and results.
                #
                result = CsvPathResult(
                    csvpath=csvpath[0], file_name=filename, paths_name=pathsname
                )
                self.path_results_manager.add_named_result(result)
                self.file_results_manager.add_named_result(result)
            except Exception as ex:
                ex.trace = traceback.format_exc()
                ex.source = self
                ErrorHandler(csvpaths=self).handle_error(ex)
