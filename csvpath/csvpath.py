import csv
import time
import os
import traceback
import hashlib
from typing import List, Dict, Any
from collections.abc import Iterator
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from csvpath.util.config import CsvPathConfig
from .util.metadata_parser import MetadataParser
from csvpath.util.log_utility import LogUtility
from csvpath.util.line_monitor import LineMonitor
from . import Error, Matcher, Scanner, ExpressionEncoder, StdOutPrinter
from . import (
    VariableException,
    InputException,
    FileException,
    ParsingException,
    FormatException,
    ProcessingException,
    ConfigurationException,
)


class CsvPathPublic(ABC):
    def parse(self, csvpath):  # pragma: no cover
        """Reads a csvpath prepares to match against CSV file lines"""
        pass

    def parse_named_path(self, name):  # pragma: no cover
        """Parses a csvpath found in this CsvPath's CsvPaths parent's collection of named csvpaths"""
        pass

    def is_valid(self) -> bool:  # pragma: no cover
        """Csvpaths can flag a CSV file as invalid using the fail() function"""
        pass

    def stop(self) -> None:  # pragma: no cover
        """Csvpaths can call for the CsvPath to stop processing lines using the stop() function"""
        pass

    def collect(self, nexts: int = -1) -> List[List[Any]]:  # pragma: no cover
        """Returns the lines of a CSV file that match the csvpath"""
        pass

    def advance(self, ff: int = -1) -> None:  # pragma: no cover
        """Advances the iteration by ff rows. The scanned rows will be considered for match and
        variables and side effects will happen, but no rows will be returned or stored.
        -1 means to the end of the file.
        """
        pass

    def fast_forward(self) -> None:  # pragma: no cover
        """Scans to the end of the CSV file. All scanned rows will be considered for match and
        variables and side effects will happen, but no rows will be returned or stored.
        -1 means to the end of the file."""
        pass

    def next(self):  # pragma: no cover
        """A generator function that steps through the CSV file returning matching rows"""
        pass


class CsvPath(CsvPathPublic):
    def __init__(
        self,
        *,
        csvpaths=None,
        delimiter=",",
        quotechar='"',
        skip_blank_lines=True,
        print_default=True,
        config=None,
    ):
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
        # self._last_line:LastLineStats = None

        #
        # the scanning part of the csvpath. e.g. $test.csv[*]
        #
        self.scan = None
        #
        # the matching part of the csvpath. e.g. [yes()]
        #
        self.match = None

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
        self._freeze_variables = False
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
        self._config = config
        #
        # there are two logger components one for CsvPath and one for CsvPaths.
        # the default levels are set in config.ini. to change the levels pass LogUtility
        # your component instance and the logging level. e.g.:
        # LogUtility.logger(csvpath, "debug")
        #
        self.logger = LogUtility.logger(self)
        self.logger.info("initialized CsvPath")

    @property
    def config(self) -> CsvPathConfig:
        if not self._config:
            self._config = CsvPathConfig()
        return self._config

    def has_errors(self) -> bool:
        if self.errors and len(self.errors) > 0:
            return True
        elif self.error_collector:
            return self.error_collector.has_errors()
        return False

    @property
    def errors(self) -> List[Error]:
        return (
            self._errors
            if self._error_collector is None
            else self._error_collector.errors
        )

    @property
    def error_collector(self):
        return self._error_collector

    @error_collector.setter
    def error_collector(self, error_collector) -> None:
        self._error_collector = error_collector

    def collect_error(self, e: Error) -> None:
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

    def add_printer(self, printer) -> None:
        if printer not in self.printers:
            self.printers.append(printer)

    def set_printers(self, printers: List) -> None:
        self.printers = printers

    def print(self, string: str) -> None:
        for p in self.printers:
            p.print(string)

    def parse(self, csvpath):
        self.scanner = Scanner(csvpath=self)
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
        self.scan = s
        self.match = mat
        self.scanner.parse(s)
        #
        # we build a matcher to see if it builds without error.
        # in principle we could keep this as the actual matcher.
        # atm, tho, just create a dry-run copy. in some possible
        # unit tests we may not have a parsable match part.
        #
        if mat:
            Matcher(csvpath=self, data=mat, line=None, headers=None)

        if self.scanner.filename is None:
            raise ConfigurationException("Cannot proceed without a filename")
        else:
            self.get_total_lines_and_headers()
        return self.scanner

    def parse_named_path(self, name):
        if not self.csvpaths:
            raise ConfigurationException("No CsvPaths object available")
        np = self.csvpaths.get_named_path(name)
        if not np:
            raise ConfigurationException(f"Named path {name} not found")
        self.parse(np)

    def _update_file_path(self, data: str):
        if data is None:
            raise InputException("The csvpath string cannot be None")
        if self.csvpaths is None:
            return data
        name = self._get_name(data)
        path = self.csvpaths.files_manager.get_named_file(name)
        if path is None:
            return data
        elif path == name:
            return data
        else:
            return data.replace(name, path)

    def _get_name(self, data: str):
        if self.csvpaths is None:
            return data
        else:
            data = data.strip()
            if data[0] == "$":
                name = data[1 : data.find("[")]
                return name
            else:
                raise FormatException(f"Must start with '$', not {data[0]}")
            return data

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
                os.path.join(self._save_scan_dir, f"{self._run_name}.txt"), "w"
            ) as f:
                f.write(scan)
        if self._save_match_dir and self._run_name:
            with open(
                os.path.join(self._save_match_dir, f"{self._run_name}.txt"), "w"
            ) as f:
                f.write(match)

    def __str__(self):
        return f"""
            path: {self.scanner.path if self.scanner else None}
            parser: {self.scanner}
            from_line: {self.scanner.from_line if self.scanner else None}
            to_line: {self.scanner.to_line if self.scanner else None}
            all_lines: {self.scanner.all_lines if self.scanner else None}
            these: {self.scanner.these if self.scanner else None}
        """

    @property
    def is_valid(self) -> bool:  # pragma: no cover
        return self._is_valid

    @is_valid.setter
    def is_valid(self, tf: bool) -> None:
        self._is_valid = tf

    @property
    def from_line(self):  # pragma: no cover
        if self.scanner is None:
            raise ParsingException("No scanner available. Have you parsed a csvpath?")
        return self.scanner.from_line

    @property
    def to_line(self):  # pragma: no cover
        if self.scanner is None:
            raise ParsingException("No scanner available. Have you parsed a csvpath?")
        return self.scanner.to_line

    @property
    def all_lines(self):  # pragma: no cover
        if self.scanner is None:
            raise ParsingException("No scanner available. Have you parsed a csvpath?")
        return self.scanner.all_lines

    @property
    def path(self):  # pragma: no cover
        if self.scanner is None:
            raise ParsingException("No scanner available. Have you parsed a csvpath?")
        return self.scanner.path

    @property
    def these(self):  # pragma: no cover
        if self.scanner is None:
            raise ParsingException("No scanner available. Have you parsed a csvpath?")
        return self.scanner.these

    @property
    def limit_collection_to(self) -> List[int]:
        return self._limit_collection_to

    @limit_collection_to.setter
    def limit_collection_to(self, indexes: List[int]) -> None:
        self._limit_collection_to = indexes
        self.logger.warning("Setting a limit on headers collected: {indexes}")

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
            elif nexts > 1:
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
                yield line
            if self.stopped:
                break
        self._freeze_variables = True
        end = time.time()
        self.total_iteration_time = end - start
        self.logger.info(f"Run against {self.scanner.filename} is complete.")
        self.logger.info(f"Iteration time was {round(self.total_iteration_time, 2)}")
        self.logger.info(
            f"{round(self.total_iteration_time / self.line_monitor.physical_end_line_count, 2)} per line."
        )

    def _next_line(self) -> List[Any]:
        self.logger.info(f"beginning to scan file: {self.scanner.filename}")
        #
        # this exception will blow up a standalone CsvPath but should be
        # caught and handled if there is a CsvPaths.
        #
        if self.scanner.filename is None:
            raise FileException("There is no filename")
        with open(self.scanner.filename, "r") as file:
            reader = csv.reader(
                file, delimiter=self.delimiter, quotechar=self.quotechar
            )
            for line in reader:
                self.track_line(line=line)
                yield line

    def track_line(self, line) -> None:
        #
        # move this here so CsvPaths can call it
        #
        last_line = None
        if self.matcher:
            last_line = self.matcher.line
        self.line_monitor.next_line(last_line=last_line, data=line)

    def _consider_line(self, line):
        #
        # we always look at the last line so that last() has a
        # chance to run
        #
        # if we're empty, but last, we need to make sure the
        # matcher runs a final time so that any last() can run.
        #
        if self.line_monitor.is_last_line_and_empty(line):
            self.logger.info(
                "last line is empty. freezing, matching, and returning false."
            )
            self._freeze_variables = True
            self.matches(line)
            return False

        blankskip = (
            # if we skip blanks
            self.skip_blank_lines
            # and the line is blank
            and len(line) == 0
        )
        if blankskip:
            # we skip this line
            self.logger.info(
                f"Skipping line {self.line_monitor.physical_line_number} because blank"
            )
            pass
        elif self.scanner.includes(self.line_monitor.physical_line_number):
            self.scan_count = self.scan_count + 1
            startmatch = time.perf_counter_ns()
            b = False
            if self._advance > 0:
                self._advance -= 1
            else:
                b = self.matches(line)
            endmatch = time.perf_counter_ns()
            if b:
                self.match_count = self.match_count + 1
                t = (endmatch - startmatch) / 1000000
                self.last_row_time = t
                self.rows_time += t
                return True
        return False

    def limit_collection(self, line: List[Any]) -> List[Any]:
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
        if self._advance > self.line_monitor.physical_end_line_number:
            self._advance = self.line_monitor.physical_end_line_number

    def get_total_lines(self) -> int:
        if (
            self.line_monitor.physical_end_line_number is None
            or self.line_monitor.physical_end_line_number == 0
        ):
            self.get_total_lines_and_headers()
        return self.line_monitor.physical_end_line_number

    def get_total_lines_and_headers(self) -> int:
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
            with open(self.scanner.filename, "r") as file:
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
                f"Counting lines and getting headers took {round(end - start, 2)}"
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
    def current_scan_count(self) -> int:
        return self.scan_count

    @property
    def current_match_count(self) -> int:
        return self.match_count

    def matches(self, line) -> bool:
        if not self.match:
            return True
        if self.matcher is None:
            h = hashlib.sha256(self.match.encode("utf-8")).hexdigest()
            self.logger.info(f"Loading matcher with data. match part hash: {h}")
            self.matcher = Matcher(
                csvpath=self, data=self.match, line=line, headers=self.headers
            )
        else:
            self.logger.info("Resetting and reloading matcher")
            self.matcher.reset()
            self.matcher.line = line
        matched = self.matcher.matches()
        return matched

    def set_variable(self, name: str, *, value: Any, tracking: Any = None) -> None:
        if self._freeze_variables:
            self.logger.warning(
                f"The run is ending, the variables are frozen. Cannot set {name} to {value}"
            )
            return
        if not name:
            raise VariableException(
                f"Name cannot be None: name: {name}, tracking: {tracking}, value: {value}"
            )
        if name.strip() == "":
            raise VariableException(
                f"Name cannot be the empty string: name: {name}, tracking: {tracking}, value: {value}"
            )
        if tracking is not None and f"{tracking}".strip() == "":
            raise VariableException(
                f"Tracking value cannot be the empty string: name: {name}, tracking: {tracking}, value: {value}"
            )
        if tracking is not None:
            if name not in self.variables:
                self.variables[name] = {}
            instances = self.variables[name]
            instances[tracking] = value
        else:
            self.variables[name] = value

    def get_variable(
        self, name: str, *, tracking: Any = None, set_if_none: Any = None
    ) -> Any:
        if not name:
            raise VariableException("Name cannot be None")
        if self._freeze_variables:
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
        if self._freeze_variables:
            if isinstance(thevalue, list):
                #
                # run is ending, no more changes
                #
                thevalue = tuple(thevalue[:])
                self.logger.debug(
                    f"Returning {thevalue} for frozen variable {name}.{tracking}"
                )
        return thevalue

    def line_numbers(self) -> Iterator[int | str]:
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
        these: List[int] = [],
        from_line: int = None,
        to_line: int = None,
        all_lines: bool = None,
    ) -> Iterator[int | str]:
        if len(these) > 0:
            for i in these:
                yield i
        else:
            if from_line is not None and to_line is not None and from_line > to_line:
                for i in range(to_line, from_line + 1):
                    yield i
            elif from_line is not None and to_line is not None:
                for i in range(from_line, to_line + 1):
                    yield i
            elif from_line is not None:
                if all_lines:
                    yield f"{from_line}..."
                else:
                    yield from_line
            elif to_line is not None:
                yield f"0..{to_line}"

    def collect_line_numbers(self) -> List[int | str]:
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
        these: List[int] = [],
        from_line: int = None,
        to_line: int = None,
        all_lines: bool = None,
    ) -> List[int | str]:
        collect = []
        for i in self._line_numbers(
            these=these, from_line=from_line, to_line=to_line, all_lines=all_lines
        ):
            collect.append(i)
        return collect

    def header_index(self, name: str) -> int:
        if not self.headers:
            return None
        for i, n in enumerate(self.headers):
            if n == name:
                return i
        return None
