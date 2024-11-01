""" CsvPaths' intent is to help you manage and automate your use
    of the CsvPath library. it makes it easier to scale your CSV quality control. """

from abc import ABC, abstractmethod
from typing import List, Any
import csv
import traceback
from .util.error import ErrorHandler, ErrorCollector, Error
from .util.config import Config
from .util.log_utility import LogUtility
from .util.metadata_parser import MetadataParser
from .util.exceptions import InputException
from .managers.csvpaths_manager import PathsManager
from .managers.file_manager import FileManager
from .managers.results_manager import ResultsManager
from .managers.result import Result
from . import CsvPath


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
    def collect_by_line(
        self, *, pathsname, filename, if_all_agree=False, collect_when_not_matched=False
    ):  # pragma: no cover
        """Does a CsvPath.collect() on filename where each row is considered
        by every named path before the next row starts

        next_by_line for if_all_agree and collect_when_not_matched.
        """

    @abstractmethod
    def fast_forward_by_line(
        self, *, pathsname, filename, if_all_agree=False, collect_when_not_matched=False
    ):  # pragma: no cover
        """Does a CsvPath.fast_forward() on filename where each row is
        considered by every named path before the next row starts

        next_by_line for if_all_agree and collect_when_not_matched.
        """

    @abstractmethod
    def next_by_line(
        self,
        *,
        pathsname,
        filename,
        collect: bool = False,
        if_all_agree=False,
        collect_when_not_matched=False,
    ) -> List[Any]:  # pragma: no cover
        """Does a CsvPath.next() on filename where each row is considered
        by every named path before the next row starts.

        if_all_agree=True means all the CsvPath instances must match for
        the line to be kept. However, every CsvPath instance will keep its
        own matches in its results regardless of if every line kept was
        returned to the caller by CsvPaths.

        collect_when_not_matched=True inverts the match so that lines
        which did not match are returned, rather than the default behavior.
        """


class CsvPathsCoordinator(ABC):
    """This abstract class defines callbacks for CsvPath instances to
    broadcast state to their siblings through CsvPaths. A CsvPath
    instance might stop the entire run, rather than each CsvPath
    instance needing to contain the same logic that stops their
    participation in a run.
    """

    @abstractmethod
    def stop_all(self) -> None:  # pragma: no cover
        """Stops every CsvPath instance in a run"""

    @abstractmethod
    def fail_all(self) -> None:  # pragma: no cover
        """Fails every CsvPath instance in a run"""

    @abstractmethod
    def skip_all(self) -> None:  # pragma: no cover
        """skips the line for every CsvPath instance in a run"""

    @abstractmethod
    def advance_all(self, lines: int) -> None:  # pragma: no cover
        """advances every CsvPath instance in a run"""


class CsvPaths(CsvPathsPublic, CsvPathsCoordinator, ErrorCollector):
    """Manages the application of csvpaths to files. Csvpaths must be grouped and named.
    Files must be named. Results are held by the results_manager.
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        *,
        delimiter=",",
        quotechar='"',
        skip_blank_lines=True,
        print_default=True,
        config: Config = None,
    ):
        self.paths_manager = PathsManager(csvpaths=self)
        self.file_manager = FileManager(csvpaths=self)
        self.results_manager = ResultsManager(csvpaths=self)
        self.print_default = print_default
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.skip_blank_lines = skip_blank_lines
        self.current_matcher: CsvPath = None
        self._config = Config() if config is None else config
        self.logger = LogUtility.logger(self)
        self.logger.info("initialized CsvPaths")
        self._errors = []
        # coordinator attributes
        self._stop_all = False
        self._fail_all = False
        self._skip_all = False
        self._advance_all = 0

    def clear_run_coordination(self) -> None:
        """run coordination is the set of signals that csvpaths send to affect
        one another through the CsvPaths instance"""
        self._stop_all = False
        self._fail_all = False
        self._skip_all = False
        self._advance_all = 0
        self.logger.debug("Cleared run coordination")

    def csvpath(self) -> CsvPath:
        path = CsvPath(
            csvpaths=self,
            delimiter=self.delimiter,
            quotechar=self.quotechar,
            skip_blank_lines=self.skip_blank_lines,
            #
            # in the usual case we don't want csvpaths and its csvpath children
            # to share the same config. sharing doesn't offer much. the flexibility
            # of having separate configs is valuable.
            #
            config=None,
            print_default=self.print_default,
        )
        return path

    def stop_all(self) -> None:  # pragma: no cover
        self._stop_all = True

    def fail_all(self) -> None:  # pragma: no cover
        self._fail_all = True

    def skip_all(self) -> None:  # pragma: no cover
        self._skip_all = True

    def advance_all(self, lines: int) -> None:  # pragma: no cover
        self._advance_all = lines

    @property
    def errors(self) -> List[Error]:  # pylint: disable=C0116
        return self._errors

    def collect_error(self, error: Error) -> None:  # pylint: disable=C0116
        self._errors.append(error)

    def has_errors(self) -> bool:  # pylint: disable=C0116
        return len(self._errors) > 0

    @property
    def config(self) -> Config:  # pylint: disable=C0116
        if not self._config:
            self._config = Config()  # pragma: no cover
        return self._config

    def clean(self, *, paths) -> None:
        """at this time we do not recommend reusing CsvPaths, but it is doable
        you should clean before reuse unless you want to accumulate results."""
        self.results_manager.clean_named_results(paths)

    def _validate_paths_and_file(self, *, pathsname, filename) -> None:
        if pathsname not in self.paths_manager.named_paths:  # pragma: no cover
            keys = list(self.paths_manager.named_paths.keys())
            raise InputException(
                f"Pathsname '{pathsname}' must be a named set of paths in {keys}"
            )
        if filename not in self.file_manager.named_files:  # pragma: no cover
            keys = self.file_manager.named_files.keys()
            raise InputException(f"Filename must be a named file in {keys}")

    def collect_paths(self, *, pathsname, filename) -> None:
        self._validate_paths_and_file(pathsname=pathsname, filename=filename)
        paths = self.paths_manager.get_named_paths(pathsname)
        file = self.file_manager.get_named_file(filename)
        self.logger.info("Cleaning out any %s and % results", filename, pathsname)
        self.clean(paths=pathsname)
        self.logger.info(
            "Beginning collect_paths %s with %s paths", pathsname, len(paths)
        )
        for path in paths:
            csvpath = self.csvpath()
            result = Result(csvpath=csvpath, file_name=filename, paths_name=pathsname)
            # casting a broad net because if "raise" not in the error policy we
            # want to never fail during a run
            try:
                self.results_manager.add_named_result(result)
                self._load_csvpath(csvpath, path=path, file=file)
                lines = csvpath.collect()
                if lines is None:
                    self.logger.error(  # pragma: no cover
                        "Unexpected None for lines after collect_paths: file: %s, match: %s",
                        file,
                        csvpath.match,
                    )
                if len(lines) == 0:
                    self.logger.warning(  # pragma: no cover
                        "No lines collected in collect_paths: file: %s match: %s",
                        file,
                        csvpath.match,
                    )
                result.lines = lines
            except Exception as ex:  # pylint: disable=W0718
                ex.trace = traceback.format_exc()
                ex.source = self
                ErrorHandler(csvpaths=self, error_collector=result).handle_error(ex)
        self.clear_run_coordination()
        self.logger.info(
            "Completed collect_paths %s with %s paths", pathsname, len(paths)
        )

    def _load_csvpath(self, csvpath: CsvPath, path: str, file: str) -> None:
        self.logger.debug("Beginning to load csvpath %s with file %s", path, file)
        # we strip comments from above the path so we need to extract them first
        path = MetadataParser(self).extract_metadata(instance=csvpath, csvpath=path)
        self.logger.debug("Csvpath after metadata extract: %s", path)
        # update the settings using the metadata fields we just collected
        csvpath.update_settings_from_metadata()
        f = path.find("[")
        self.logger.debug("Csvpath matching part starts at char # %s", f)
        apath = f"${file}{path[f:]}"
        self.logger.info("Parsing csvpath %s", apath)
        csvpath.parse(apath)

    def fast_forward_paths(self, *, pathsname, filename):
        self._validate_paths_and_file(pathsname=pathsname, filename=filename)
        paths = self.paths_manager.get_named_paths(pathsname)
        file = self.file_manager.get_named_file(filename)
        self.logger.info("Cleaning out any %s and %s results", filename, pathsname)
        self.clean(paths=pathsname)
        self.logger.info(
            "Beginning FF %s with %s paths against file %s. No match results will be held.",
            pathsname,
            len(paths),
            filename,
        )
        for i, path in enumerate(paths):
            csvpath = self.csvpath()
            self.logger.debug("Beginning to FF CsvPath instance: %s", csvpath)
            result = Result(csvpath=csvpath, file_name=filename, paths_name=pathsname)
            try:
                self.results_manager.add_named_result(result)
                self._load_csvpath(csvpath, path=path, file=file)
                self.logger.info(
                    "Parsed csvpath %s pointed at %s and starting to fast-forward",
                    i,
                    file,
                )
                csvpath.fast_forward()
                self.logger.info(
                    "Completed fast forward of csvpath %s against %s", i, file
                )
            except Exception as ex:  # pylint: disable=W0718
                ex.trace = traceback.format_exc()
                ex.source = self
                ErrorHandler(csvpaths=self, error_collector=result).handle_error(ex)
        self.clear_run_coordination()
        self.logger.info(
            "Completed fast_forward_paths %s with %s paths", pathsname, len(paths)
        )

    def next_paths(self, *, pathsname, filename, collect: bool = False):
        """appends the Result for each CsvPath to the end of
        each line it produces. this is so that the caller can easily
        interrogate the CsvPath for its path parts, file, etc."""
        self._validate_paths_and_file(pathsname=pathsname, filename=filename)
        paths = self.paths_manager.get_named_paths(pathsname)
        file = self.file_manager.get_named_file(filename)
        self.logger.info("Cleaning out any %s and %s results", filename, pathsname)
        self.clean(paths=pathsname)
        self.logger.info("Beginning next_paths with %s paths", len(paths))
        for path in paths:
            if self._skip_all:
                skip_err = "Found the skip-all signal set. skip_all() is"
                skip_err = f"{skip_err} only for breadth-first runs using the"
                skip_err = f"{skip_err} '_by_line' methods. It has the same"
                skip_err = f"{skip_err} effect as skip() in a"
                skip_err = f"{skip_err} serial run like this one."
                self.logger.error(skip_err)
            if self._stop_all:
                self.logger.warning("Stop-all set. Shutting down run.")
                break
            if self._advance_all > 0:
                advance_err = "Found the advance-all signal set. advance_all() is"
                advance_err = f"{advance_err} only for breadth-first runs using the"
                advance_err = f"{advance_err} '_by_line' methods. It has the same"
                advance_err = f"{advance_err} effect as advance() in a"
                advance_err = f"{advance_err} serial run like this one."
                self.logger.error(advance_err)
            csvpath = self.csvpath()
            result = Result(csvpath=csvpath, file_name=filename, paths_name=pathsname)
            if self._fail_all:
                self.logger.warning(
                    "Fail-all set. Failing all remaining CsvPath instances in the run."
                )
                csvpath.is_valid = False
            try:
                self.results_manager.add_named_result(result)
                self._load_csvpath(csvpath, path=path, file=file)
                for line in csvpath.next():
                    line.append(result)
                    if collect:
                        result.append(line)
                    yield line
            except Exception as ex:  # pylint: disable=W0718
                ex.trace = traceback.format_exc()
                ex.source = self
                ErrorHandler(csvpaths=self, error_collector=result).handle_error(ex)
        self.clear_run_coordination()

    # =============== breadth first processing ================

    def collect_by_line(
        self, *, pathsname, filename, if_all_agree=False, collect_when_not_matched=False
    ):
        self.logger.info(
            "Starting collect_by_line for paths: %s and file: %s", pathsname, filename
        )
        lines = []
        for line in self.next_by_line(  # pylint: disable=W0612
            pathsname=pathsname,
            filename=filename,
            collect=True,
            if_all_agree=if_all_agree,
            collect_when_not_matched=collect_when_not_matched,
        ):
            # re: W0612: we need 'line' in order to do the iteration. we have to iterate.
            lines.append(line)
        self.logger.info(
            "Completed collect_by_line for paths: %s and file: %s", pathsname, filename
        )
        #
        # the results have all the lines according to what CsvPath captured them, but
        # since we're doing if_all_agree T/F we should return the union here. for some
        # files this obviously makes the data in memory problem even bigger, but it's
        # operator's responsibility to know if that will be a problem for their use
        # case.
        #
        return lines

    def fast_forward_by_line(
        self, *, pathsname, filename, if_all_agree=False, collect_when_not_matched=False
    ):
        self.logger.info(
            "Starting fast_forward_by_line for paths: %s and file: %s",
            pathsname,
            filename,
        )
        for line in self.next_by_line(  # pylint: disable=W0612
            pathsname=pathsname,
            filename=filename,
            collect=False,
            if_all_agree=if_all_agree,
            collect_when_not_matched=collect_when_not_matched,
        ):
            # re: W0612: we need 'line' in order to do the iteration. we have to iterate.
            pass
        self.logger.info(
            "Completed fast_forward_by_line for paths: %s and file: %s",
            pathsname,
            filename,
        )

    def next_by_line(  # pylint: disable=R0912
        self,
        *,
        pathsname,
        filename,
        collect: bool = False,
        if_all_agree=False,
        collect_when_not_matched=False,
    ) -> List[Any]:
        # re: R0912 -- absolutely. plan to refactor.
        self.logger.info("Cleaning out any %s and %s results", filename, pathsname)
        self._validate_paths_and_file(pathsname=pathsname, filename=filename)
        self.clean(paths=pathsname)
        fn = self.file_manager.get_named_file(filename)
        paths = self.paths_manager.get_named_paths(pathsname)
        if (
            paths is None or not isinstance(paths, list) or len(paths) == 0
        ):  # pragma: no cover
            raise InputException(
                f"Pathsname '{pathsname}' must name a list of csvpaths"
            )
        csvpath_objects = self._load_csvpath_objects(
            paths=paths,
            named_file=fn,
            collect_when_not_matched=collect_when_not_matched,
        )
        self._prep_csvpath_results(
            csvpath_objects=csvpath_objects, filename=filename, pathsname=pathsname
        )
        #
        # setting fn into the csvpath is less obviously useful at CsvPaths
        # but we'll do it for consistency.
        #
        self.logger.info("Beginning next_by_line with %s paths", len(csvpath_objects))
        """
        with open(fn, "r", encoding="utf-8") as file:
            reader = csv.reader(
                file, delimiter=self.delimiter, quotechar=self.quotechar
            )  # pylint: disable=R1702
            #
            # re: R1702 -- totally agreed! deferring.
            #
        """
        reader = FileManager.get_reader(
            fn, delimiter=self.delimiter, quotechar=self.quotechar
        )
        stopped_count: List[int] = []
        for line in reader.next():
            # for line in reader:  # pylint: disable=R1702
            # question to self: should this default be in a central place
            # so that we can switch to OR, in part by changing the default?
            keep = if_all_agree
            self._skip_all = False
            self._advance_all = 0
            try:
                # p is a (CsvPath, List[List[str]]) where the second item is
                # the line-by-line results of the first item's matching
                for p in csvpath_objects:
                    self.current_matcher = p[0]
                    if self._fail_all:
                        self.logger.warning(
                            "Fail-all set. Setting CsvPath is_valid to False."
                        )
                        self.current_matcher.is_valid = False
                    if self._stop_all:
                        self.logger.warning("Stop-all set. Shutting down run.")
                        self.current_matcher.stopped = True
                        continue
                    if self._skip_all:
                        self.logger.warning("Skip-all set. Continuing to next.")
                        #
                        # all following CsvPaths must have their
                        # line_monitors incremented
                        #
                        self.current_matcher.track_line(line)
                        continue
                    if self._advance_all > 0:
                        logtxt = "Advance-all set. Setting advance. "
                        logtxt = f"{logtxt}CsvPath and its Matcher will handle the advancing."
                        self.logger.info(logtxt)
                        #
                        # CsvPath will handle advancing so we don't need to do
                        # anything, including track_line(line). we just need to
                        # see if we're setting advance or increasing it.
                        #
                        a = self.current_matcher.advance_count
                        if self._advance_all > a:
                            self.current_matcher.advance_count = self._advance_all
                        #
                        # all following CsvPaths must have their
                        # advance incremented -- with the advance not being simply
                        # additive, have to be mindful of any existing advance
                        # count!
                        #
                    if self.current_matcher.stopped:  # pylint: disable=R1724
                        continue

                    #
                    # allowing the match to happen regardless of keep
                    # because we may want side-effects or to have different
                    # results in different named-results, as well as the
                    # union
                    #
                    self.logger.debug(
                        "considering line with csvpath identified as: %s",
                        self.current_matcher.identity,
                    )
                    matched = False
                    self.current_matcher.track_line(line)
                    #
                    # re: W0212: treating _consider_line something like package private
                    #
                    matched = (
                        self.current_matcher._consider_line(  # pylint:disable=W0212
                            line
                        )
                    )
                    if self.current_matcher.stopped:
                        stopped_count.append(1)
                    if if_all_agree:
                        keep = keep and matched
                    else:
                        keep = keep or matched
                    #
                    # not doing continue if we have if_all_agree and not keep as we
                    # used to do allows individual results to have lines that in
                    # aggregate we do not keep.
                    #
                    if matched and collect:
                        line = self.current_matcher.limit_collection(line)
                        p[1].append(line)
            except Exception as ex:  # pylint: disable=W0718
                ex.trace = traceback.format_exc()
                ex.source = self
                ErrorHandler(
                    csvpaths=self, error_collector=self.current_matcher
                ).handle_error(ex)
            # we yield even if we stopped in this iteration.
            # caller needs to see what we stopped on.
            #
            # ! we only yield if keep is True
            #
            if keep:
                yield line
            if sum(stopped_count) == len(csvpath_objects):
                break
        self.clear_run_coordination()

    def _load_csvpath_objects(
        self, *, paths: List[str], named_file: str, collect_when_not_matched=False
    ):
        csvpath_objects = []
        for path in paths:
            csvpath = self.csvpath()
            csvpath.collect_when_not_matched = collect_when_not_matched
            try:
                self._load_csvpath(csvpath, path=path, file=named_file)
                csvpath_objects.append([csvpath, []])
            except Exception as ex:  # pylint: disable=W0718
                ex.trace = traceback.format_exc()
                ex.source = self
                # the error handler is the Results. it registers itself with
                # the csvpath as the error collector. not as straightforward a way to
                # get ErrorHandler what it needs, but effectively same as we do above
                ErrorHandler(csvpaths=self, error_collector=csvpath).handle_error(
                    ex
                )  # pragma: no cover
        return csvpath_objects

    def _prep_csvpath_results(self, *, csvpath_objects, filename, pathsname):
        for csvpath in csvpath_objects:
            try:
                #
                # Result will set itself into its CsvPath as error collector
                # printer, etc.
                #
                result = Result(
                    csvpath=csvpath[0],
                    file_name=filename,
                    paths_name=pathsname,
                    lines=csvpath[1],
                )
                csvpath[1] = result
                self.results_manager.add_named_result(result)
            except Exception as ex:  # pylint: disable=W0718
                ex.trace = traceback.format_exc()
                ex.source = self
                ErrorHandler(csvpaths=self, error_collector=csvpath).handle_error(ex)
                #
                # keep this comment for modelines avoidance
                #
