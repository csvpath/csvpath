""" CsvPaths' intent is to help you manage and automate your use
    of the CsvPath library. it makes it easier to scale your CSV quality control. """

from abc import ABC, abstractmethod
from typing import List, Any, Tuple
import csv
import traceback
from csvpath.util.error import ErrorHandler
from csvpath.util.config import CsvPathConfig
from csvpath.util.log_utility import LogUtility
from csvpath.util.metadata_parser import MetadataParser
from . import CsvPath
from . import ConfigurationException
from . import PathsManager, FilesManager
from . import ResultsManager, CsvPathResult


class CsvPathsPublic(ABC):
    """this abstract class is the public interface for CsvPaths.

    a CsvPaths instance manages applying any number of csvpaths
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

    @abstractmethod
    def collect_paths(self, *, pathsname, filename) -> None:  # pragma: no cover
        """Sequentially does a CsvPath.collect() on filename for every named path"""

    @abstractmethod
    def fast_forward_paths(self, *, pathsname, filename) -> None:  # pragma: no cover
        """Sequentially does a CsvPath.fast_forward() on filename for every named path"""

    @abstractmethod
    def next_paths(self, *, pathsname, filename) -> None:  # pragma: no cover
        """Does a CsvPath.next() on filename for every line against every named path in sequence"""

    @abstractmethod
    def collect_by_line(self, *, pathsname, filename):  # pragma: no cover
        """Does a CsvPath.collect() on filename where each row is considered
        by every named path before the next row starts"""

    @abstractmethod
    def fast_forward_by_line(self, *, pathsname, filename):  # pragma: no cover
        """Does a CsvPath.fast_forward() on filename where each row is
        considered by every named path before the next row starts"""

    @abstractmethod
    def next_by_line(
        self, *, pathsname, filename, collect: bool = False
    ) -> List[Any]:  # pragma: no cover
        """Does a CsvPath.next() on filename where each row is considered
        by every named path before the next row starts"""


class CsvPaths(CsvPathsPublic):
    """Manages the application of csvpaths to files. Csvpaths must be grouped and named.
    Files must be named. Results are held by the results_manager.
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self, *, delimiter=",", quotechar='"', skip_blank_lines=True, print_default=True
    ):
        self.paths_manager = PathsManager(csvpaths=self)
        self.files_manager = FilesManager(csvpaths=self)
        self.results_manager = ResultsManager(csvpaths=self)
        self.print_default = print_default
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.skip_blank_lines = skip_blank_lines
        self.current_matcher: CsvPath = None
        self.config = CsvPathConfig()
        self.logger = LogUtility.logger(self)
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

    def clean(self, *, paths) -> None:
        """at this time we do not recommend reusing CsvPaths, but it is doable
        you should clean before reuse unless you want to accumulate results."""
        self.results_manager.clean_named_results(paths)

    def collect_paths(self, *, pathsname, filename) -> None:
        if pathsname not in self.paths_manager.named_paths:
            raise ConfigurationException("Pathsname must be a named set of paths")
        if filename not in self.files_manager.named_files:
            raise ConfigurationException("Filename must be a named file")
        paths = self.paths_manager.get_named_paths(pathsname)
        file = self.files_manager.get_named_file(filename)
        self.logger.info("Cleaning out any %s and % results", filename, pathsname)
        self.clean(paths=pathsname)
        self.logger.info(
            "Beginning collect_paths %s with %s paths", pathsname, len(paths)
        )
        for path in paths:
            csvpath = self.csvpath()
            result = CsvPathResult(
                csvpath=csvpath, file_name=filename, paths_name=pathsname
            )
            try:
                self.results_manager.add_named_result(result)
                self._load_csvpath(csvpath, path=path, file=file)
                lines = csvpath.collect()
                result.lines = lines
            except Exception as ex:  # pylint: disable=W0718
                ex.trace = traceback.format_exc()
                ex.source = self
                ErrorHandler(
                    logger=self.logger, error_collector=result, component="csvpaths"
                ).handle_error(ex)
        self.logger.info(
            "Completed collect_paths %s with %s paths", pathsname, len(paths)
        )

    def _load_csvpath(self, csvpath: CsvPath, path: str, file: str) -> None:
        # we strip comments from above the path so we need to extract them first
        path = MetadataParser().extract_metadata(instance=csvpath, csvpath=path)
        # csvpath._extract_metadata(path)
        f = path.find("[")
        apath = f"${file}{path[f:]}"
        csvpath.parse(apath)

    def fast_forward_paths(self, *, pathsname, filename):
        if pathsname not in self.paths_manager.named_paths:
            raise ConfigurationException("pathsname must be a named set of paths")
        if filename not in self.files_manager.named_files:
            raise ConfigurationException("Filename must be a named file")
        paths = self.paths_manager.get_named_paths(pathsname)
        file = self.files_manager.get_named_file(filename)
        self.logger.info("Cleaning out any %s and %s results", filename, pathsname)
        self.clean(paths=pathsname)
        self.logger.info(
            "Beginning fast_forward_paths %s with %s paths", pathsname, len(paths)
        )
        for i, path in enumerate(paths):
            csvpath = self.csvpath()
            result = CsvPathResult(
                csvpath=csvpath, file_name=filename, paths_name=pathsname
            )
            try:
                self.results_manager.add_named_result(result)
                self._load_csvpath(csvpath, path=path, file=file)
                self.logger.info("Parsed csvpath %s pointed at %s", i, file)
                csvpath.fast_forward()
                self.logger.info(
                    "Completed fast forward of csvpath %s against %s", i, file
                )
            except Exception as ex:  # pylint: disable=W0718
                ex.trace = traceback.format_exc()
                ex.source = self
                ErrorHandler(
                    logger=self.logger, error_collector=result, component="csvpaths"
                ).handle_error(ex)
        self.logger.info(
            "Completed fast_forward_paths %s with %s paths", pathsname, len(paths)
        )

    def next_paths(self, *, pathsname, filename):
        """appends the CsvPathResult for each CsvPath to the end of
        each line it produces. this is so that the caller can easily
        interrogate the CsvPath for its path parts, file, etc."""
        if pathsname not in self.paths_manager.named_paths:
            raise ConfigurationException(
                f"Pathsname '{pathsname}' must be a named set of paths"
            )
        if filename not in self.files_manager.named_files:
            raise ConfigurationException(f"Filename '{filename}' must be a named file")
        paths = self.paths_manager.get_named_paths(pathsname)
        file = self.files_manager.get_named_file(filename)
        self.logger.info("Cleaning out any %s and %s results", filename, pathsname)
        self.clean(paths=pathsname)
        self.logger.info("Beginning next_paths with %s paths", len(paths))
        for path in paths:
            csvpath = self.csvpath()
            result = CsvPathResult(
                csvpath=csvpath, file_name=filename, paths_name=pathsname
            )
            try:
                self.results_manager.add_named_result(result)
                self._load_csvpath(csvpath, path=path, file=file)
                for line in csvpath.next():
                    line.append(result)
                    yield line
            except Exception as ex:  # pylint: disable=W0718
                ex.trace = traceback.format_exc()
                ex.source = self
                ErrorHandler(
                    logger=self.logger, error_collector=result, component="csvpaths"
                ).handle_error(ex)

    # =============== breadth first processing ================

    def collect_by_line(self, *, pathsname, filename):
        self.logger.info(
            "Starting collect_by_line for paths: %s and file: %s", pathsname, filename
        )
        for line in self.next_by_line(  # pylint: disable=W0612
            pathsname=pathsname, filename=filename, collect=True
        ):
            # re: W0612: we need 'line' in order to do the iteration. we have to iterate.
            pass
        self.logger.info(
            "Completed collect_by_line for paths: %s and file: %s", pathsname, filename
        )

    def fast_forward_by_line(self, *, pathsname, filename):
        self.logger.info(
            "Starting fast_forward_by_line for paths: %s and file: %s",
            pathsname,
            filename,
        )
        for line in self.next_by_line(  # pylint: disable=W0612
            pathsname=pathsname, filename=filename, collect=False
        ):
            # re: W0612: we need 'line' in order to do the iteration. we have to iterate.
            pass
        self.logger.info(
            "Completed fast_forward_by_line for paths: %s and file: %s",
            pathsname,
            filename,
        )

    def next_by_line(  # pylint: disable=R0912
        self, *, pathsname, filename, collect: bool = False
    ) -> List[Any]:
        # re: R0912 -- absolutely does have too many branches. will refactor later.
        self.logger.info("Cleaning out any %s and %s results", filename, pathsname)
        self.clean(paths=pathsname)
        if filename not in self.files_manager.named_files:
            raise ConfigurationException(f"Filename '{filename}' must be a named file")
        fn = self.files_manager.get_named_file(filename)
        if not fn:
            raise ConfigurationException(f"Filename '{filename}' must be a named file")
        if pathsname not in self.paths_manager.named_paths:
            raise ConfigurationException(
                f"Pathsname '{pathsname}' must name a set of csvpaths"
            )
        paths = self.paths_manager.get_named_paths(pathsname)
        if not isinstance(paths, list) or len(paths) == 0:
            raise ConfigurationException(
                f"Pathsname '{pathsname}' must name a list of csvpaths"
            )

        csvpath_objects = self._load_csvpath_objects(paths=paths, named_file=fn)
        self._prep_csvpath_results(
            csvpath_objects=csvpath_objects, filename=filename, pathsname=pathsname
        )
        #
        # setting fn into the csvpath is less obviously useful at CsvPaths
        # but we'll do it for consistency.
        #
        self.logger.info("Beginning next_by_line with %s paths", len(csvpath_objects))
        with open(fn, "r", encoding="utf-8") as file:
            reader = csv.reader(
                file, delimiter=self.delimiter, quotechar=self.quotechar
            )  # pylint: disable=R1702
            #
            # re: R1702 -- totally agreed! deferring.
            #
            stopped_count: List[int] = []
            for line in reader:  # pylint: disable=R1702
                # note to self: this default should be determined in a central place
                # so that we can switch to OR, in part by changing the default to False
                line_matched = True
                try:
                    #
                    # p is a (CsvPath, List[List[str]]) where the second item is
                    # the line by line results of the first item's matching
                    for p in csvpath_objects:
                        self.current_matcher = p[0]
                        if self.current_matcher.stopped:  # pylint: disable=R1724
                            # using if/else and continue just to be over-clear
                            continue
                        else:
                            self.current_matcher.track_line(line)
                            #
                            # re: W0212: treating _consider_line something like package private
                            #
                            matched = self.current_matcher._consider_line(  # pylint:disable=W0212
                                line
                            )
                            line_matched = line_matched and matched
                            if matched and collect:
                                line = self.current_matcher.limit_collection(line)
                                p[1].append(line)
                            if matched or self.current_matcher.stopped:
                                if self.current_matcher.stopped:
                                    stopped_count.append(1)
                except Exception as ex:  # pylint: disable=W0718
                    ex.trace = traceback.format_exc()
                    ex.source = self
                    ErrorHandler(
                        logger=self.logger,
                        error_collector=self.current_matcher,
                        component="csvpaths",
                    ).handle_error(ex)
                # we yield even if we stopped in this iteration.
                # caller needs to see what we stopped on.
                yield line
                if sum(stopped_count) == len(csvpath_objects):
                    break
                # note to self: we have the lines in p[1]. we could, optionally, iteratively
                # move them to the results here. probably a future requirement.

    def _load_csvpath_objects(
        self, *, paths: List[str], named_file: str
    ) -> List[Tuple[CsvPath, List]]:
        csvpath_objects = []
        for path in paths:
            csvpath = self.csvpath()
            try:
                self._load_csvpath(csvpath, path=path, file=named_file)
                csvpath_objects.append((csvpath, []))
            except Exception as ex:  # pylint: disable=W0718
                ex.trace = traceback.format_exc()
                ex.source = self
                # the error handler is the CsvPathResults. it registers itself with
                # the csvpath as the error collector. not as straightforward a way to
                # get ErrorHandler what it needs, but effectively same as we do above
                ErrorHandler(
                    logger=self.logger, error_collector=csvpath, component="csvpaths"
                ).handle_error(ex)
        return csvpath_objects

    def _prep_csvpath_results(self, *, csvpath_objects, filename, pathsname):
        for csvpath in csvpath_objects:
            try:
                #
                # lines object is a shared reference between path and results.
                # CsvPathResult will set itself into its CsvPath as error collector
                # printer, etc.
                #
                result = CsvPathResult(
                    csvpath=csvpath[0], file_name=filename, paths_name=pathsname
                )
                self.results_manager.add_named_result(result)
            except Exception as ex:  # pylint: disable=W0718
                ex.trace = traceback.format_exc()
                ex.source = self
                ErrorHandler(
                    logger=self.logger, error_collector=csvpath, component="csvpaths"
                ).handle_error(ex)
