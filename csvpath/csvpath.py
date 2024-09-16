""" CsvPath is the main class for the library. most of the magic
    happens either here or in individual functions. """

import csv
import time
import os
import hashlib
from typing import List, Dict, Any
from collections.abc import Iterator
from abc import ABC, abstractmethod
from csvpath.util.config import CsvPathConfig
from csvpath.util.line_monitor import LineMonitor
from csvpath.util.log_utility import LogUtility
from .matching.matcher import Matcher
from .scanning.scanner import Scanner
from .util.metadata_parser import MetadataParser
from .util.error import Error
from .util.printer import StdOutPrinter
from .util.exceptions import VariableException, InputException, ParsingException
from .util.exceptions import (
    FileException,
    FormatException,
    ProcessingException,
    CsvPathsException,
)
from .matching.util.exceptions import MatchException


class CsvPathPublic(ABC):
    """this abstract class is the public interface for CsvPath"""

    @abstractmethod
    def parse(self, csvpath):  # pragma: no cover
        """Reads a csvpath prepares to match against CSV file lines"""

    @abstractmethod
    def parse_named_path(self, name):  # pragma: no cover
        """Parses a csvpath found in this CsvPath's CsvPaths parent's
        collection of named csvpaths"""

    @property
    @abstractmethod
    def is_valid(self) -> bool:  # pragma: no cover
        """Csvpaths can flag a CSV file as invalid using the fail() function"""

    @abstractmethod
    def stop(self) -> None:  # pragma: no cover
        """Csvpaths can call for the CsvPath to stop processing lines
        using the stop() function"""

    @abstractmethod
    def collect(self, nexts: int = -1) -> List[List[Any]]:  # pragma: no cover
        """Returns the lines of a CSV file that match the csvpath"""

    @abstractmethod
    def advance(self, ff: int = -1) -> None:  # pragma: no cover
        """Advances the iteration by ff rows. The scanned rows will be
        considered for match and variables and side effects will happen,
        but no rows will be returned or stored. -1 means to the end of
        the file.
        """

    @abstractmethod
    def fast_forward(self) -> None:  # pragma: no cover
        """Scans to the end of the CSV file. All scanned rows will be
        considered for match and variables and side effects will happen,
        but no rows will be returned or stored. -1 means to the end of
        the file."""

    @abstractmethod
    def next(self):  # pragma: no cover
        """A generator function that steps through the CSV file returning
        matching rows"""


class CsvPath(CsvPathPublic):  # pylint: disable=R0902, R0904
    """CsvPath represents a csvpath string that contains a reference to
    a file, scanning instructions, and rules for matching lines.
    """

    # re R0902, R0904: reasonable, but not a priority

    def __init__(  # pylint: disable=R0913
        self,
        *,
        csvpaths=None,
        delimiter=",",
        quotechar='"',
        skip_blank_lines=True,
        print_default=True,
        config=None,
    ):
        # re: R0913: all reasonable pass-ins with sensible defaults
        self.scanner = None
        self.matcher = None
        #
        # a parent CsvPaths may manage a CsvPath instance. if so, it will enable
        # the use of named files and named paths, print capture, error handling,
        # results collection, reference handling, etc. if a CsvPaths is not present
        # the CsvPath instance is responsible for all its own upkeep and does not have
        # some of those capabilities.
        #
        self.csvpaths = csvpaths
        #
        #
        #
        self.line_monitor = LineMonitor()
        #
        # the scanning part of the csvpath. e.g. $test.csv[*]
        #
        self.scan = None
        #
        # the matching part of the csvpath. e.g. [yes()]
        #
        self.match = None
        #
        # when AND is True we do a logical AND of the match components
        # to see if there is a match. this is the default. when AND is
        # False (or set OR to True) the match components are ORed to
        # determine if a line matches. in the former case all the match
        # components must agree for a line to match. in the latter case,
        # if any one match component votes True the line is matched.
        # technically you can switch from AND to OR, or vice versa, in
        # the middle of iterating a file using next(). probably not a
        # good idea, tho.
        #
        self._AND = True
        #
        # when True the lines that do not match are returned from next()
        # and collect(). this effectively switches CsvPath from being an
        # AND machine to being a NOT AND machine. we do not actually
        # create an OR expression in this case. in the default, we say:
        #     are all of these things true?
        # but when collect_when_not_matched is True we ask:
        #     are any of these things not true?
        #
        self._when_not_matched = False
        self.headers = None
        self.variables: Dict[str, Any] = {}
        self.delimiter = delimiter
        self.quotechar = quotechar
        #
        # a blank line has no headers. it has no data. physically it is 2 \n with
        # nothing but whitespace between them. any data or any delimiters would make
        # the line non-blank.
        #
        self.skip_blank_lines = skip_blank_lines
        #
        # in the case of a [*] scan where the last line is blank we would miss firing
        # last() unless we take steps. instead, we allow that line to match, but we
        # do not return a line to the caller of next() and we freeze the variables
        # there is room for side effects make changes, but that a reasonable compromise
        # between missing last and allowing unwanted changes. we definitely do not
        # freeze is_valid or stop, which can be useful signaling, even in an
        # inconsistent state.
        #
        self._freeze_path = False
        #
        # counts are 1-based
        #
        self.scan_count = 0
        self.match_count = 0
        #
        # used by stop() and advance(). a stopped CsvPath halts without finishing
        # its run. an advancing CsvPath doesn't consider the match part of the
        # csvpath and does not incur any side effects as it progresses through the
        # rows the advance skips. the skip() function has the same effect as
        # advance(1) but without any guarantee that the other match components on
        # the line will be considered before skipping ahead. there are likely
        # corner cases where an onmatch qualifier or some other constraint will
        # trigger match components that would otherwise be skipped so the ability
        # to shortcut some of the match should not be relied on for anything
        # critical.
        #
        self.stopped = False
        self._advance = 0
        #
        # set by fail()
        #
        self._is_valid = True
        #
        # basic timing for the CsvPath instance only. if the CsvPath is managed
        # by a CsvPaths the timings for a run may include time spent by other
        # CsvPath instances.
        #
        self.last_row_time = -1
        self.rows_time = -1
        self.total_iteration_time = -1
        #
        # limiting collection means returning fewer headers (values in the
        # line, a.k.a columns) then are available. limiting headers returned
        # can impact named results, reset_headers(), and other considerations.
        #
        self._limit_collection_to = []
        #
        # error collecting is at the CsvPath instance by default. CsvPath
        # instances that are managed by a CsvPaths have their errors collected
        # by their ResultsManager. the policy for errors -- their noise level,
        # effect on validity, etc. -- is set in config.ini at the CsvPath and
        # CsvPaths level.
        #
        self._errors: List[Error] = None
        self._error_collector = None
        #
        # saves the scan and match parts of paths for reference. mainly helpful
        # for testing the CsvPath library itself; not used end users. the run
        # name becomes the file name of the saved path parts.
        #
        self._save_scan_dir = None
        self._save_match_dir = None
        self._run_name = None
        #
        # metadata is collected from "outer" csvpath comments. outer comments
        # separate from the comments within the match part of the csvpath.
        # the keys are words with colons. e.g. ~ name: my new csvpath ~
        #
        self.metadata: Dict[str, Any] = {}
        #
        # holds the current match count while we're in the middle of a match
        # so that anyone who wants to can increase the match count using
        # raise_match_count_if(). it is important to do the raise asap so that
        # components that are onmatched have the right match count available.
        #
        self._current_match_count = 0
        #
        # printers receive print lines from the print function. the default
        # printer prints to standard out. a CsvPath that is managed by a
        # CsvPaths has its CsvPathResults as a printer, as well as having
        # the default printer.
        #
        self.printers = []
        if print_default:
            self.printers.append(StdOutPrinter())
        #
        # the config.ini file loaded as a ConfigParser instance
        #
        # we're moving this to a property can set up there. we
        # definitely do not want this coming from CsvPaths because
        # we want to be able to override config.ini specifically for
        # this instance, if needed.
        self._config = None
        #
        # there are two logger components one for CsvPath and one for CsvPaths.
        # the default levels are set in config.ini. to change the levels pass LogUtility
        # your component instance and the logging level. e.g.:
        # LogUtility.logger(csvpath, "debug")
        #
        self.logger = LogUtility.logger(self)
        self.logger.info("initialized CsvPath")

    @property
    def AND(self) -> bool:
        return self._AND

    @AND.setter
    def AND(self, a: bool) -> bool:
        self._AND = a

    @property
    def OR(self) -> bool:
        return not self._AND

    @OR.setter
    def OR(self, a: bool) -> bool:
        self._AND = not a

    @property
    def identity(self) -> str:
        """returns id or name if found in metadata. the id or name gets
        into metadata primarily if found in an "external" comment in
        the csvpath. "external" meaning outside the []s. comments are
        keyword:comment. we take id, Id, ID and name, Name, NAME. id
        is preferred over name. E.g.:
        ~ name: my path description: an example ~
        """
        if not self.metadata:
            return ""
        if "id" in self.metadata:
            return self.metadata["id"]
        if "Id" in self.metadata:
            return self.metadata["Id"]
        if "ID" in self.metadata:
            return self.metadata["ID"]
        if "name" in self.metadata:
            return self.metadata["name"]
        if "Name" in self.metadata:
            return self.metadata["Name"]
        if "NAME" in self.metadata:
            return self.metadata["NAME"]
        return ""

    @property
    def config(self) -> CsvPathConfig:  # pylint: disable=C0116
        if not self._config:
            self._config = CsvPathConfig(self)
        return self._config

    def has_errors(self) -> bool:  # pylint: disable=C0116
        if self.errors and len(self.errors) > 0:
            return True
        if self.error_collector:
            return self.error_collector.has_errors()
        return False

    @property
    def errors(self) -> List[Error]:  # pylint: disable=C0116
        return (
            self._errors
            if self._error_collector is None
            else self._error_collector.errors
        )

    @property
    def error_collector(self):  # pylint: disable=C0116
        return self._error_collector

    @error_collector.setter
    def error_collector(self, error_collector) -> None:
        self._error_collector = error_collector

    def collect_error(self, e: Error) -> None:  # pylint: disable=C0116
        #
        # errors must be built and handled in ErrorHandler.
        # here we're just collecting them if collect is
        # selected by our configuration
        #
        if self._error_collector:
            self._error_collector.collect_error(e)
        else:
            if self._errors is None:
                self._errors = []
            self._errors.append(e)

    def add_printer(self, printer) -> None:  # pylint: disable=C0116
        if printer not in self.printers:
            self.printers.append(printer)

    def set_printers(self, printers: List) -> None:  # pylint: disable=C0116
        self.printers = printers

    def print(self, string: str) -> None:  # pylint: disable=C0116
        for p in self.printers:
            p.print(string)

    @property
    def is_frozen(self) -> bool:
        return self._freeze_path

    @is_frozen.setter
    def is_frozen(self, freeze: bool) -> None:
        self._freeze_path = freeze

    @property
    def collect_when_not_matched(self) -> bool:
        """when this property is True CsvPath returns the lines that do not
        match the matcher's match components
        """
        return self._when_not_matched

    @collect_when_not_matched.setter
    def collect_when_not_matched(self, yesno: bool) -> None:
        """when collect_when_not_matched is True we return the lines that failed
        to match, rather than the default behavior of returning the matches.
        """
        self._when_not_matched = yesno

    def parse(self, csvpath, disposably=False):
        """displosably is True when a Matcher is needed for some purpose other than
        the run we were created to do. could be that a match component wanted a
        parsed csvpath for its own purposes. when True, we create and return the
        Matcher, but then forget it ever existed.

        when disposably is False we build the scanner and return that
        """
        #
        # strip off any comments and collect any metadata
        # CsvPaths will do this earlier but it stripped off
        # the comments so we won't find them again
        #
        csvpath = MetadataParser().extract_metadata(instance=self, csvpath=csvpath)
        #
        #
        #
        csvpath = self._update_file_path(csvpath)
        s, mat = self._find_scan_and_match_parts(csvpath)
        #
        # a disposable matcher still needs the match part
        #
        self.match = mat
        if disposably:
            pass
        else:
            self.scan = s
            self.scanner = Scanner(csvpath=self)
            self.scanner.parse(s)
        #
        # we build a matcher to see if it builds without error.
        # in principle we could keep this as the actual matcher.
        # atm, tho, just create a dry-run copy. in some possible
        # unit tests we may not have a parsable match part.
        #
        matcher = None
        if mat:
            matcher = Matcher(csvpath=self, data=mat, line=None, headers=None)
        if disposably:
            #
            # if the matcher was requested for some reason beyond our own needs
            # we just return it and forget it existed.
            #
            return matcher
        if self.scanner.filename is None:
            raise FileException("Cannot proceed without a filename")
        self.get_total_lines_and_headers()
        return self.scanner

    def parse_named_path(self, name, disposably=False):
        """disposably is True when a Matcher is needed for some purpose other than
        the run we were created to do. could be that a match component wanted a
        parsed csvpath for its own purposes. import() uses this method.

        when True, we create and return the Matcher, but then forget it ever existed.

        also note: the path must have a name or full filename. $[*] is not enough.
        """
        if not self.csvpaths:
            raise CsvPathsException("No CsvPaths object available")
        np = self.csvpaths.paths_manager.get_named_paths(name)
        if not np:
            raise CsvPathsException(f"Named paths {name} not found")
        if len(np) == 0:
            raise CsvPathsException(f"Named paths {name} has no csvpaths")
        if len(np) > 1:
            self.logger.warning(
                "parse_named_path %s has %s csvpaths. Parsing just the first one.",
                name,
                len(np),
            )
        path = np[0]
        path = MetadataParser().extract_metadata(instance=self, csvpath=path)
        path = self._update_file_path(path)
        dis = self.parse(path, disposably=disposably)
        if disposably is True:
            return dis
        return None

    def _update_file_path(self, data: str):
        """this method replaces a name (i.e. name in: $name[*[][yes()]) with
        a file system path, if that name is registered with csvpaths's file
        manager. if there is no csvpaths no replace happens. if there is a
        csvpaths but the file manager doesn't know the name, no replace
        happens.
        """
        if data is None:
            raise InputException("The csvpath string cannot be None")
        if self.csvpaths is None:
            return data
        name = self._get_name(data)
        path = self.csvpaths.files_manager.get_named_file(name)
        if path is None:
            return data
        if path == name:
            return data
        return data.replace(name, path)

    def _get_name(self, data: str):
        if self.csvpaths is None:
            return data
        data = data.strip()
        if data[0] == "$":
            name = data[1 : data.find("[")]
            return name
        raise FormatException(f"Must start with '$', not {data[0]}")

    def _find_scan_and_match_parts(self, data):
        if data is None or not isinstance(data, str):
            raise InputException("Not a csvpath string")
        scan = ""
        matches = ""

        i = data.find("]")
        if i < 0:
            raise InputException(f"Cannot find the scan part of this csvpath: {data}")

        scan = data[0 : i + 1]
        scan = scan.strip()

        ndata = data[i + 1 :]
        ndata = ndata.strip()

        if ndata == "":
            raise InputException("There must be a match part of this csvpath: {data}")

        if ndata[0] != "[":
            raise InputException("Cannot find the match part of this csvpath: {data}")
        if ndata[len(ndata) - 1] != "]":
            raise InputException("The match part of this csvpath is incorrect: {data}")
        matches = ndata
        #
        # if we're given directory(s) to save to, save the parts
        #
        self._save_parts_if(scan, matches)
        return scan, matches

    def _save_parts_if(self, scan, match):
        if self._save_scan_dir and self._run_name:
            with open(
                os.path.join(self._save_scan_dir, f"{self._run_name}.txt"),
                "w",
                encoding="utf-8",
            ) as f:
                f.write(scan)
        if self._save_match_dir and self._run_name:
            with open(
                os.path.join(self._save_match_dir, f"{self._run_name}.txt"),
                "w",
                encoding="utf-8",
            ) as f:
                f.write(match)

    def __str__(self):
        return f"""
            path: {self.scanner.path if self.scanner else None}
            parsers: [scanner=Ply, matcher=Lark, print=Lark]
            from_line: {self.scanner.from_line if self.scanner else None}
            to_line: {self.scanner.to_line if self.scanner else None}
            all_lines: {self.scanner.all_lines if self.scanner else None}
            these: {self.scanner.these if self.scanner else None}
            matcher: {self.matcher}
            variables: {len(self.variables)}
            metadata: {len(self.metadata)}
        """

    @property
    def is_valid(self) -> bool:  # pragma: no cover
        return self._is_valid

    @is_valid.setter
    def is_valid(self, tf: bool) -> None:
        self._is_valid = tf

    @property
    def from_line(self):  # pragma: no cover pylint: disable=C0116
        if self.scanner is None:
            raise ParsingException("No scanner available. Have you parsed a csvpath?")
        return self.scanner.from_line

    @property
    def to_line(self):  # pragma: no cover pylint: disable=C0116
        if self.scanner is None:
            raise ParsingException("No scanner available. Have you parsed a csvpath?")
        return self.scanner.to_line

    @property
    def all_lines(self):  # pragma: no cover pylint: disable=C0116
        if self.scanner is None:
            raise ParsingException("No scanner available. Have you parsed a csvpath?")
        return self.scanner.all_lines

    @property
    def path(self):  # pragma: no cover pylint: disable=C0116
        if self.scanner is None:
            raise ParsingException("No scanner available. Have you parsed a csvpath?")
        return self.scanner.path

    @property
    def these(self):  # pragma: no cover pylint: disable=C0116
        if self.scanner is None:
            raise ParsingException("No scanner available. Have you parsed a csvpath?")
        return self.scanner.these

    @property
    def limit_collection_to(self) -> List[int]:
        """returns the list of headers to collect when a line matches. by default
        this list is empty and all headers are collected.
        """
        return self._limit_collection_to

    @limit_collection_to.setter
    def limit_collection_to(self, indexes: List[int]) -> None:
        self._limit_collection_to = indexes
        self.logger.warning("Setting a limit on headers collected: %s", indexes)

    def stop(self) -> None:
        self.stopped = True

    #
    #
    # collect(), fast_forward(), and next() are the central methods of CsvPath.
    #
    #
    def collect(self, nexts: int = -1) -> List[List[Any]]:
        """Runs the csvpath forward and returns the matching lines seen as
        a list of lists"""
        if nexts < -1:
            raise ProcessingException(
                "Input must be >= -1. -1 means collect to the end of the file."
            )
        lines = []
        for _ in self.next():
            _ = _[:]
            lines.append(_)
            if nexts == -1:
                continue
            if nexts > 1:
                nexts -= 1
            else:
                break
        return lines

    def fast_forward(self) -> None:
        """Runs the path for all rows of the file. Variables are collected
        and side effects like print happen. No lines are collected.
        """
        for _ in self.next():
            pass

    def next(self):
        """Iterates over the lines in the CSV file returning those that match
        the csvpath. collect() and fast_forward() call next() behind the scenes.
        """
        start = time.time()
        for line in self._next_line():
            b = self._consider_line(line)
            if b:
                line = self.limit_collection(line)
                if line is None:
                    msg = "Line cannot be None"
                    self.logger.error(msg)
                    raise MatchException(msg)
                elif len(line) == 0:
                    msg = "Line cannot be len() == 0"
                    self.logger.error(msg)
                    raise MatchException(msg)
                yield line
            if self.stopped:
                break
        self.finalize()
        # moving to finalize
        # self._freeze_path = True
        end = time.time()
        self.total_iteration_time = end - start
        self.logger.info("Run against %s is complete.", self.scanner.filename)
        self.logger.info("Iteration time was %s", round(self.total_iteration_time, 2))
        self.logger.info(
            "%s per line",
            round(
                self.total_iteration_time / self.line_monitor.physical_end_line_count, 2
            ),
        )

    def _next_line(self) -> List[Any]:
        self.logger.info("beginning to scan file: %s", self.scanner.filename)
        #
        # this exception will blow up a standalone CsvPath but should be
        # caught and handled if there is a CsvPaths.
        #
        if self.scanner.filename is None:
            raise FileException("There is no filename")
        with open(self.scanner.filename, "r", encoding="utf-8") as file:
            reader = csv.reader(
                file, delimiter=self.delimiter, quotechar=self.quotechar
            )
            for line in reader:
                self.track_line(line=line)
                yield line
        self.finalize()

    def finalize(self) -> None:
        """clears caches, etc. this is an internal method, but not _ because
        it is part of the lifecycle and we might find a reason to call it
        from higher up.
        """
        # this method can run multiple times w/np, but that
        # shouldn't happen anyway.
        self._freeze_path = True
        self.matcher.clear_caches()

    def track_line(self, line) -> None:
        """csvpaths needs to handle some of the iteration logic, and we don't want
        to lose track of line number monitoring or repeat the code up there,
        so we need this method to give csvpaths a way to tap in.
        """
        last_line = None
        if self.matcher:
            last_line = self.matcher.line
        self.line_monitor.next_line(last_line=last_line, data=line)

    def _consider_line(self, line):  # pylint: disable=R0912, R0911
        # re: R0912: this method has already been refactored but maybe
        # there is more we can do?
        #
        # we always look at the last line so that last() has a
        # chance to run
        #
        # if we're empty, but last, we need to make sure the
        # matcher runs a final time so that any last() can run.
        #
        if self.line_monitor.is_last_line_and_blank(line):
            # if self.line_monitor.is_last_line_and_empty(line):
            self.logger.info("last line is empty. freezing, matching, returning false")
            self._freeze_path = True
            self.matches(line)
            return False
        if self.skip_blank_lines and len(line) == 0:
            self.logger.info(
                "Skipping line %s because blank", self.line_monitor.physical_line_number
            )
            return False
        if self.scanner.includes(self.line_monitor.physical_line_number):
            self.logger.debug("Scanner includes line")
            self.scan_count = self.scan_count + 1
            matches = None
            self._current_match_count = self.match_count
            if self._advance > 0:
                self._advance -= 1
                matches = False
                self.logger.debug(
                    "Advancing one line with {self._advance} more skips to go"
                )
            else:
                self.logger.debug("Starting matching")
                startmatch = time.perf_counter_ns()
                matches = self.matches(line)
                endmatch = time.perf_counter_ns()
                t = (endmatch - startmatch) / 1000000
                self.last_row_time = t
                self.rows_time += t
                self.logger.debug(
                    "CsvPath.matches:703: %s: matches: %s", self.identity, matches
                )
            if matches is True:
                #
                # _current_match_count is a placeholder that
                # allows anyone to call a match early and update
                # the count. this is important when there is
                # an onmatch component that needs to use the
                # match_count. e.g. an onmatch print statement.
                # we would want the onmatch to propagate asap. we
                # can accept that there could be a variable set to
                # match count prior to the onmatch upping the
                # count. that wouldn't be great for explainability,
                # but order is important -- match components
                # impact each other left to right, top to bottom.
                #
                self.raise_match_count_if()
                if self.collect_when_not_matched:
                    return False
                return True
            if self.collect_when_not_matched:
                return True
            return False
        return False

    def raise_match_count_if(self):
        if self._current_match_count == self.match_count:
            self.match_count += 1
        else:
            self.logger.debug("Match count was already raised, so not doing it again")

    def limit_collection(self, line: List[Any]) -> List[Any]:
        """this method creates a line based on the given line that holds only the headers
        that the csvpath says to collect. headers for collection are indicated using
        the collect() function.
        """
        if len(self.limit_collection_to) == 0:
            return line
        ls = []
        for k in self.limit_collection_to:
            ls.append(line[k])
        return ls

    def advance(self, ff: int = -1) -> None:
        """Advances the iteration by ff rows. The rows will be seen and
        variables and side effects will happen.
        """
        if ff is None:
            raise InputException("Input to advance must not be None")
        if self.line_monitor.physical_end_line_number is None:
            raise ProcessingException(
                "The last line number must be known (physical_end_line_number)"
            )
        if ff == -1:
            self._advance = (
                self.line_monitor.physical_end_line_number
                - self.line_monitor.physical_line_number
                - self._advance
            )
        else:
            self._advance += ff
        self._advance = min(self._advance, self.line_monitor.physical_end_line_number)

    def get_total_lines(self) -> int:  # pylint: disable=C0116
        if (
            self.line_monitor.physical_end_line_number is None
            or self.line_monitor.physical_end_line_number == 0
        ):
            self.get_total_lines_and_headers()
        return self.line_monitor.physical_end_line_number

    def get_total_lines_and_headers(self) -> int:  # pylint: disable=C0116
        #
        # total lines is a count not a pointer. counts are 1-based
        # pointers are array indexes, so they are 0-based.
        #
        if (
            self.line_monitor.physical_end_line_number is None
            or self.line_monitor.physical_end_line_number == -1
        ):
            start = time.time()
            self.line_monitor.reset()
            with open(self.scanner.filename, "r", encoding="utf-8") as file:
                reader = csv.reader(
                    file, delimiter=self.delimiter, quotechar=self.quotechar
                )
                for line in reader:
                    self.track_line(line)
                    # self.line_monitor.next_line(last_line=None, data=line)
                    if len(line) == 0 and self.skip_blank_lines:
                        continue
                    if (not self.headers or len(self.headers) == 0) and len(line) > 0:
                        self.headers = line[:]
            if not self.headers:
                self.headers = []
            self._clean_headers()
            end = time.time()
            self.logger.info(
                "Counting lines and getting headers took %s", round(end - start, 2)
            )
            self.line_monitor.set_end_lines_and_reset()

    def _clean_headers(self) -> None:
        if self.headers is None:
            self.logger.warning("Cannot clean headers because headers are None")
            return
        hs = self.headers[:]
        self.headers = []
        for header in hs:
            header = header.strip()
            header = header.replace(";", "")
            header = header.replace(",", "")
            header = header.replace("|", "")
            header = header.replace("\t", "")
            header = header.replace("`", "")
            self.headers.append(header)

    @property
    def current_scan_count(self) -> int:  # pylint: disable=C0116
        return self.scan_count

    @property
    def current_match_count(self) -> int:  # pylint: disable=C0116
        return self.match_count

    def matches(self, line) -> bool:  # pylint: disable=C0116
        if not self.match:
            return True
        #
        # when we first consider a line we don't have a matcher. we build
        # it on the fly. later, we just reset the matcher for the new lines.
        #
        # when we originally call parse we're just parsing for the scanner:
        #
        #   path = CsvPath()
        #   path.parse ("$file[*][yes()]")
        #   path.fast_forward()
        #
        # "find_file" would be a more intuitive method name. we don't create
        # the path's matcher until the 3rd line. by then we're on the 3rd parser
        # and 4 parse.
        #
        if self.matcher is None:
            h = hashlib.sha256(self.match.encode("utf-8")).hexdigest()
            self.logger.info("Loading matcher with data. match part hash: %s", h)
            self.matcher = Matcher(
                csvpath=self, data=self.match, line=line, headers=self.headers, myid=h
            )
            self.matcher._AND = self._AND
        else:
            self.logger.debug("Resetting and reloading matcher")
            self.matcher.reset()
            self.matcher.line = line
        matched = self.matcher.matches()
        return matched

    def set_variable(self, name: str, *, value: Any, tracking: Any = None) -> None:
        """sets a variable and the tracking variable as a key within
        it, if a tracking value is provided."""
        if self._freeze_path:
            self.logger.warning(
                "Run is ending, variables are frozen. Cannot set %s to %s.", name, value
            )
            return
        if not name:
            raise VariableException(
                f"Name cannot be None: name: {name}, tracking: {tracking}, value: {value}"
            )
        if name.strip() == "":
            raise VariableException(
                f"""Name cannot be the empty string:
                    name: {name}, tracking: {tracking}, value: {value}"""
            )
        if tracking is not None and f"{tracking}".strip() == "":
            raise VariableException(
                f"""Tracking value cannot be empty.
                    name: {name}, tracking: {tracking}, value: {value}"""
            )
        if tracking is not None:
            if name not in self.variables:
                self.variables[name] = {}
            instances = self.variables[name]
            instances[tracking] = value
        else:
            self.variables[name] = value

    def get_variable(  # pylint: disable=R0912
        self, name: str, *, tracking: Any = None, set_if_none: Any = None
    ) -> Any:
        """gets a variable by name. uses the tracking value as a key to get
        the value if the variable is a dictionary."""
        #
        # re: R0912: totally true. this is a scary method. plan to refactor.
        #
        if not name:
            raise VariableException("Name cannot be None")
        if self._freeze_path:
            #
            # run is ending, no more changes
            #
            set_if_none = None
        thevalue = None
        if tracking is not None:
            thedict = None
            thevalue = None
            if name in self.variables:
                thedict = self.variables[name]
                if not thedict:
                    thedict = {}
                    self.variables[name] = thedict
                    thedict[tracking] = set_if_none
            else:
                thedict = {}
                thedict[tracking] = set_if_none
                self.variables[name] = thedict
            if isinstance(thedict, dict):
                thevalue = thedict.get(tracking)
            if not thevalue and set_if_none is not None:
                thedict[tracking] = set_if_none
                thevalue = set_if_none
        else:
            if name not in self.variables:
                if set_if_none is not None:
                    self.variables[name] = set_if_none
                    thevalue = set_if_none
            else:
                thevalue = self.variables[name]
        if self._freeze_path:
            if isinstance(thevalue, list):
                #
                # run is ending, no more changes
                #
                thevalue = tuple(thevalue[:])
                self.logger.debug(
                    "Returning %s for frozen variable %s.%s", thevalue, name, tracking
                )
        return thevalue

    def line_numbers(self) -> Iterator[int | str]:
        """returns all the line numbers the scanner will scan during
        the run of a csvpath"""
        these = self.scanner.these
        from_line = self.scanner.from_line
        to_line = self.scanner.to_line
        all_lines = self.scanner.all_lines
        return self._line_numbers(
            these=these, from_line=from_line, to_line=to_line, all_lines=all_lines
        )

    def _line_numbers(
        self,
        *,
        these: List[int] = None,
        from_line: int = None,
        to_line: int = None,
        all_lines: bool = None,
    ) -> Iterator[int | str]:
        if these is None:
            these = []
        if len(these) > 0:
            yield from these
        else:
            if from_line is not None and to_line is not None and from_line > to_line:
                yield from range(to_line, from_line + 1)
            elif from_line is not None and to_line is not None:
                yield from range(from_line, to_line + 1)
            elif from_line is not None:
                if all_lines:
                    yield f"{from_line}..."
                else:
                    yield from_line
            elif to_line is not None:
                yield f"0..{to_line}"

    def collect_line_numbers(self) -> List[int | str]:  # pylint: disable=C0116
        if self.scanner is None:
            raise ParsingException("No scanner available. Have you parsed a csvpath?")
        these = self.scanner.these
        from_line = self.scanner.from_line
        to_line = self.scanner.to_line
        all_lines = self.scanner.all_lines
        return self._collect_line_numbers(
            these=these, from_line=from_line, to_line=to_line, all_lines=all_lines
        )

    def _collect_line_numbers(
        self,
        *,
        these: List[int] = None,
        from_line: int = None,
        to_line: int = None,
        all_lines: bool = None,
    ) -> List[int | str]:
        collect = []
        if these is None:
            these = []
        for i in self._line_numbers(
            these=these, from_line=from_line, to_line=to_line, all_lines=all_lines
        ):
            collect.append(i)
        return collect

    def header_index(self, name: str) -> int:  # pylint: disable=C0116
        if not self.headers:
            return None
        for i, n in enumerate(self.headers):
            if n == name:
                return i
        return None
