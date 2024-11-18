""" CsvPath is the main class for the library. most of the magic
    happens either here or in individual functions. """

import csv
import time
import os
import hashlib
from datetime import datetime
from typing import List, Dict, Any
from collections.abc import Iterator
from abc import ABC, abstractmethod
from csvpath.util.config import Config
from csvpath.util.line_monitor import LineMonitor
from csvpath.util.log_utility import LogUtility
from .matching.matcher import Matcher
from .scanning.scanner import Scanner
from .util.metadata_parser import MetadataParser
from .util.error import Error, ErrorCollector, ErrorCommsManager
from .util.printer import StdOutPrinter
from .util.line_counter import LineCounter
from .util.exceptions import VariableException, InputException, ParsingException
from .util.exceptions import (
    FileException,
    FormatException,
    ProcessingException,
    CsvPathsException,
)
from .matching.util.exceptions import MatchException
from csvpath.util.printer import Printer
from csvpath.util.file_readers import DataFileReader


class CsvPathPublic(ABC):
    """this abstract class is the public interface for CsvPath"""

    @abstractmethod
    def parse(self, csvpath):  # pragma: no cover
        """Reads a csvpath prepares to match against CSV file lines. This
        method is an alternative to simply passing the csvpath string to the
        collect, next, or fast_forward methods. You don't do both.
        """

    @abstractmethod
    def parse_named_path(
        self, name, *, disposably=False, specific=None
    ):  # pragma: no cover
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
    def collect(
        self, csvpath: str = None, *, nexts: int = -1
    ) -> List[List[Any]]:  # pragma: no cover
        """Returns the lines of a CSV file that match the csvpath. Pass
        nexts to limit a run to collecting only N lines; the default
        is -1 for collecting all. If you do not pass the csvpath
        string here you must first use the parse method."""

    @abstractmethod
    def advance(self, ff: int = -1) -> None:  # pragma: no cover
        """Advances the iteration by ff rows. -1 means to the end of the file."""

    @abstractmethod
    def fast_forward(self, csvpath: str = None) -> None:  # pragma: no cover
        """Scans to the end of the CSV file. All scanned rows will be
        considered for match and variables and side effects will happen,
        but no rows will be returned or stored. -1 means to the end of
        the file. If you do not pass the csvpath string here you must first
        use the parse method."""

    @abstractmethod
    def next(self, csvpath: str = None):  # pragma: no cover
        """A generator function that steps through the CSV file returning
        matching rows. If you do not pass the csvpath string here you must
        first use the parse method."""


class CsvPath(CsvPathPublic, ErrorCollector, Printer):  # pylint: disable=R0902, R0904
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
        self._line_monitor = None
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
        self._AND = True  # pylint: disable=C0103
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
        self._headers = None
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
        # explain-mode: explain
        # turns on capturing match reasoning and dumps the captured decisions to INFO
        # at the end of a match. the reasoning is already present in the DEBUG but it
        # is harder to see amid all the noise. we don't want to dump explainations
        # all the time tho because it is very expensive -- potentially 25% worse
        # performance. the explainations could be improved. atm this is an experimental
        # feature.
        #
        self._explain = False
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
        # CsvPaths has its Results as a printer, as well as having
        # the default printer.
        #
        self.printers = []
        if print_default:
            self.printers.append(StdOutPrinter())
        #
        # the config.ini file loaded as a ConfigParser instance
        #
        # definitely do not want this coming from CsvPaths because
        # we want to be able to override config.ini specifically for
        # this instance, if needed; however, we do want to be able
        # to pass in a config object that has been configured in some
        # way.
        self._config = config
        #
        # these settings determine how we report function args validation
        # errors. e.g. if print(True) the validation check fails because
        # print() expects a string. the more recent trend is to get all
        # the errors and print statements in the same place controlled by
        # the same properties. for now this stays because there is a minor
        # benefit to being able to suppress runtime arg validation and only
        # use match component rules and exceptions to generate validation
        # info. but long term this capability may go away.
        #
        self._log_validation_errors = True
        self._print_validation_errors = True
        self._raise_validation_errors = None
        self._match_validation_errors = None
        self._stop_on_validation_errors = None
        self._fail_on_validation_errors = None
        #
        # run mode determines if a csvpath gets run or if it is skipped. the
        # main reasons to set run-mode: no-run vs. run are: you want to import
        # it into other csvpaths that are in the same named-paths group, or
        # you want to switch off a csvpath in a named-paths group for testing
        # a similar reason.
        #
        self._run_mode = True
        #
        # there are two logger components one for CsvPath and one for CsvPaths.
        # the default levels are set in config.ini. to change the levels pass LogUtility
        # your component instance and the logging level. e.g.:
        # LogUtility.logger(csvpath, "debug")
        #
        self.logger = LogUtility.logger(self)
        self.logger.info("initialized CsvPath")
        self._ecoms = ErrorCommsManager(csvpath=self)
        self._function_times_match = {}
        self._function_times_value = {}
        self._created_at = datetime.now()
        self._run_started_at = None

        self._collecting = False
        self._unmatched = None
        self._unmatched_available = False
        self._data_from_preceding = False

    @property
    def data_from_preceding(self) -> bool:
        return self._data_from_preceding

    @data_from_preceding.setter
    def data_from_preceding(self, dfp: bool) -> None:
        self._data_from_preceding = dfp

    @property
    def unmatched(self) -> list[list[Any]]:
        return self._unmatched

    @unmatched.setter
    def unmatched(self, lines: list[list[Any]]) -> None:
        self._unmatched = lines

    @property
    def collecting(self) -> bool:
        return self._collecting

    @collecting.setter
    def collecting(self, c: bool) -> None:
        self._collecting = c

    def set_unmatched_availability(self) -> None:
        um = self.metadata.get("unmatched-mode")
        if um is not None and um.find("no-keep") > -1:
            self.unmatched_available = False
        elif um is not None and um.find("keep") > -1:
            self.unmatched_available = True
        else:
            self.unmatched_available = False

    @property
    def unmatched_available(self) -> bool:
        return self._unmatched_available

    @unmatched_available.setter
    def unmatched_available(self, ua: bool) -> None:
        self._unmatched_available = ua

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def run_started_at(self) -> datetime:
        return self._run_started_at

    @property
    def run_mode(self) -> bool:
        return self._run_mode

    @run_mode.setter
    def run_mode(self, mode) -> None:
        self._run_mode = mode

    def _up_function_time_match(self, c, t) -> None:
        if c not in self.function_times_match:
            self.function_times_match[c] = 0
        st = self.function_times_match[c]
        st += t
        self.function_times_match[c] = st

    @property
    def function_times_match(self) -> int:
        return self._function_times_match

    def _up_function_time_value(self, c, t) -> None:
        if c not in self.function_times_value:
            self.function_times_value[c] = 0
        st = self.function_times_value[c]
        st += t
        self.function_times_value[c] = st

    @property
    def function_times_value(self) -> int:
        return self._function_times_value

    def do_i_raise(self) -> bool:
        return self._ecoms.do_i_raise()

    @property
    def advance_count(self) -> int:  # pragma: no cover
        return self._advance

    @advance_count.setter
    def advance_count(self, lines: int) -> None:
        self._advance = lines

    @property
    def headers(self) -> List[str]:
        if self._headers is None:
            self.get_total_lines_and_headers()
        return self._headers

    @headers.setter
    def headers(self, headers: List[str]) -> None:
        self._headers = headers

    @property
    def line_monitor(self) -> LineMonitor:
        if self._line_monitor is None:
            self.get_total_lines_and_headers()
        return self._line_monitor

    @line_monitor.setter
    def line_monitor(self, lm) -> None:
        self._line_monitor = lm

    @property
    def AND(self) -> bool:  # pylint: disable=C0103
        return self._AND

    @AND.setter
    def AND(self, a: bool) -> bool:  # pylint: disable=C0103
        self._AND = a

    @property
    def OR(self) -> bool:  # pylint: disable=C0103
        return not self._AND

    @OR.setter
    def OR(self, a: bool) -> bool:  # pylint: disable=C0103
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
    def config(self) -> Config:  # pylint: disable=C0116
        if not self._config:
            self._config = Config()
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

    def collect_error(self, error: Error) -> None:  # pylint: disable=C0116
        #
        # errors must be built and handled in ErrorHandler.
        # here we're just collecting them if collect is
        # selected by our configuration
        #
        if self._error_collector is not None:
            self._error_collector.collect_error(error)
        else:
            if self._errors is None:
                self._errors = []
            self._errors.append(error)

    #
    # validation error handling overrides the error policy in config. this
    # is because the validation handling is:
    #   - different. it is built-in. it deals with programmatic decisions
    #     about how functions work and is the basis for structural (schema)
    #     validation.
    #   - set on a per csvpath basis in comments
    #
    # by default, validation errors do not impact matching. they are print
    # and raise only. however, you can set them to raise or match/not-match
    # and/or suppress printing.
    #
    def set_validation_error_handling(self, veh) -> None:
        # print prints to the Printer(s), not std.out. atm, no
        # customization of messages is possible, so there is likely
        # to be stylistic mismatch with other output.
        if veh and veh.find("no-print") > -1:
            self._print_validation_errors = False
        elif veh and veh.find("print") > -1:
            self._print_validation_errors = True
        else:
            self._print_validation_errors = None
        #
        if veh and veh.find("no-raise") > -1:
            self._raise_validation_errors = False
        elif veh and veh.find("raise") > -1:
            self._raise_validation_errors = True
        else:
            self._raise_validation_errors = None
        #
        # match, no-match, and None do:
        #   match: return True on error
        #   no-match: return False on error
        #   None: default behavior: default_match() or result of matches()
        if veh and veh.find("no-match") > -1:
            self._match_validation_errors = False
        elif veh and veh.find("match") > -1:
            self._match_validation_errors = True
        else:
            self._match_validation_errors = None
        #
        # also stop and fail to match the config
        #
        if veh and veh.find("no-stop") > -1:
            self._stop_on_validation_errors = False
        elif veh and veh.find("stop") > -1:
            self._stop_on_validation_errors = True
        else:
            self._stop_on_validation_errors = None
        #
        if veh and veh.find("no-fail") > -1:
            self._fail_on_validation_errors = False
        elif veh and veh.find("fail") > -1:
            self._fail_on_validation_errors = True
        else:
            self._fail_on_validation_errors = None

    @property
    def stop_on_validation_errors(self) -> bool:
        return self._stop_on_validation_errors

    @property
    def fail_on_validation_errors(self) -> bool:
        return self._fail_on_validation_errors

    @property
    def print_validation_errors(self) -> bool:
        return self._print_validation_errors

    @property
    def log_validation_errors(self) -> bool:
        return self._log_validation_errors

    @property
    def raise_validation_errors(self) -> bool:
        return self._raise_validation_errors

    @property
    def match_validation_errors(self) -> bool:
        return self._match_validation_errors

    def add_printer(self, printer) -> None:  # pylint: disable=C0116
        if printer not in self.printers:
            self.printers.append(printer)

    def set_printers(self, printers: List) -> None:  # pylint: disable=C0116
        self.printers = printers

    @property
    def has_default_printer(self) -> bool:
        if not self.printers:
            self.printers = []
        for i, p in enumerate(self.printers):
            if isinstance(p, StdOutPrinter):
                return True
        return False

    def print(self, string: str) -> None:  # pylint: disable=C0116
        for p in self.printers:
            p.print(string)

    def print_to(self, name: str, string: str) -> None:
        for p in self.printers:
            p.print_to(name, string)

    @property
    def last_line(self):
        if not self.printers or len(self.printers) == 0:
            return None
        return self.printers[0].last_line

    @property
    def lines_printed(self) -> int:
        if not self.printers or len(self.printers) == 0:
            return -1
        self.printers[0].lines_printed

    @property
    def is_frozen(self) -> bool:
        """True if the instance is matching on its last row only to
        allow last()s to run; in which case, no variable updates
        are allowed, along with other limitations."""
        return self._freeze_path

    @is_frozen.setter
    def is_frozen(self, freeze: bool) -> None:
        self._freeze_path = freeze

    @property
    def explain(self) -> bool:
        """when this property is True CsvPath dumps a match explaination
        to INFO. this can be expensive. a 25% performance hit wouldn't
        be unexpected.
        """
        return self._explain

    @explain.setter
    def explain(self, yesno: bool) -> None:
        self._explain = yesno

    @property
    def collect_when_not_matched(self) -> bool:
        """when this property is True CsvPath returns the lines that do not
        match the matchers match components"""
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
        csvpath = MetadataParser(self).extract_metadata(instance=self, csvpath=csvpath)
        self.update_settings_from_metadata()
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
        if disposably:
            matcher = None
            if mat:
                matcher = Matcher(csvpath=self, data=mat, line=None, headers=None)
            #
            # if the matcher was requested for some reason beyond our own needs
            # we just return it and forget it existed.
            #
            return matcher
        if self.scanner.filename is None:
            raise FileException("Cannot proceed without a filename")
        self.get_total_lines_and_headers()
        return self

    def update_settings_from_metadata(self) -> None:
        #
        # settings:
        #   - logic-mode: AND | OR
        #   - return-mode: matches | no-matches
        #   - print-mode: default | no-default
        #   - validation-mode: (no-)print | log | (no-)raise | quiet | (no-)match
        #   - run-mode: no-run | run
        #   - unmatched-mode: no-keep | keep
        #   - source-mode: preceding | origin
        #
        self.update_logic_mode_if()
        self.update_run_mode_if()
        self.update_match_mode_if()
        self.update_print_mode_if()
        self.update_explain_mode_if()
        self.update_arg_validation_mode_if()
        self.update_unmatched_mode_if()
        self.update_data_from_preceding_if()

    def update_data_from_preceding_if(self) -> None:
        if self.metadata and "source-mode" in self.metadata:
            dfp = self.metadata["source-mode"]
            self.data_from_preceding = dfp == "preceding"
        else:
            self.data_from_preceding = False

    def update_unmatched_mode_if(self) -> None:
        self.set_unmatched_availability()

    def update_arg_validation_mode_if(self) -> None:
        if self.metadata and "validation-mode" in self.metadata:
            # sets arg validation reporting. one or more or none of:
            #  - print
            #  - log
            #  - raise
            #
            validation_mode = f"{self.metadata['validation-mode']}".strip()
            if validation_mode:
                self.set_validation_error_handling(validation_mode)
                self.logger.info(
                    "Setting 'validation-mode': %s",
                    self.metadata["validation-mode"],
                )

    def update_run_mode_if(self) -> None:
        if self.metadata and "run-mode" in self.metadata:
            if f"{self.metadata['run-mode']}".strip() == "no-run":
                self.run_mode = False
            elif f"{self.metadata['run-mode']}".strip() == "run":
                self.run_mode = True
            else:
                self.logger.warning(
                    "Incorrect metadata field value 'run-mode': %s",
                    self.metadata["run-mode"],
                )

    def update_logic_mode_if(self) -> None:
        if self.metadata and "logic-mode" in self.metadata:
            if f"{self.metadata['logic-mode']}".strip() == "AND":
                self.AND = True
            elif f"{self.metadata['logic-mode']}".strip() == "OR":
                self.AND = False
            else:
                self.logger.warning(
                    "Incorrect metadata field value 'logic-mode': %s",
                    self.metadata["logic-mode"],
                )

    def update_match_mode_if(self) -> None:
        if "return-mode" in self.metadata:
            if f"{self.metadata['return-mode']}".strip() == "matches":
                self.collect_when_not_matched = False
            elif f"{self.metadata['return-mode']}".strip() == "no-matches":
                self.collect_when_not_matched = True
            else:
                self.logger.warning(
                    "Incorrect metadata field value 'return-mode': %s",
                    self.metadata["return-mode"],
                )

    def update_explain_mode_if(self) -> None:
        if "explain-mode" in self.metadata:
            if f"{self.metadata['explain-mode']}".strip() == "no-explain":
                self._explain = False
            elif f"{self.metadata['explain-mode']}".strip() == "explain":
                self._explain = True
            else:
                self._explain = False

    def update_print_mode_if(self) -> None:
        if "print-mode" in self.metadata:
            if f"{self.metadata['print-mode']}".strip() == "no-default":
                remove = -1
                for i, p in enumerate(self.printers):
                    if isinstance(p, StdOutPrinter):
                        remove = i
                        break
                if remove >= 0:
                    del self.printers[remove]
            elif f"{self.metadata['print-mode']}".strip() == "default":
                done = False
                for i, p in enumerate(self.printers):
                    if isinstance(p, StdOutPrinter):
                        done = True
                        break
                if not done:
                    self.printers.append(StdOutPrinter())
            else:
                self.logger.warning(
                    "Incorrect metadata field value 'print-mode': %s",
                    self.metadata["print-mode"],
                )

    def _pick_named_path(self, name, *, specific=None) -> str:
        if not self.csvpaths:
            raise CsvPathsException("No CsvPaths object available")
        np = self.csvpaths.paths_manager.get_named_paths(name)
        if not np:
            raise CsvPathsException(f"Named-paths '{name}' not found")
        if len(np) == 0:
            raise CsvPathsException(f"Named-paths '{name}' has no csvpaths")
        if len(np) == 1:
            return np[0]
        if specific is None:
            self.logger.warning(
                "Parse_named_path %s has %s csvpaths. Using just the first one.",
                name,
                len(np),
            )
            return np[0]
        for p in np:
            # this ends up being redundant to the caller. we do it 1x so it's not
            # a big lift and is consistent.
            c = CsvPath()
            MetadataParser(c).extract_metadata(instance=c, csvpath=p)
            if c.identity == specific:
                return p
        self.logger.error(
            "Cannot find csvpath identified as %s in named-paths %s", specific, name
        )
        raise ParsingException(f"Cannot find path '{specific}' in named-paths '{name}'")

    def parse_named_path(self, name, *, disposably=False, specific=None):
        """disposably is True when a Matcher is needed for some purpose other than
        the run we were created to do. could be that a match component wanted a
        parsed csvpath for its own purposes. import() uses this method.
        when True, we create and return the Matcher, but then forget it ever existed.
        also note: the path must have a name or full filename. $[*] is not enough.
        """
        if not self.csvpaths:
            raise CsvPathsException("No CsvPaths object available")

        path = self._pick_named_path(name, specific=specific)
        c = CsvPath()
        path = MetadataParser(c).extract_metadata(instance=c, csvpath=path)
        path = c._update_file_path(path)
        dis = c.parse(path, disposably=disposably)
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
        path = self.csvpaths.file_manager.get_named_file(name)
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
        data = data.strip()
        i = data.find("]")
        if i < 0:
            raise InputException(f"Cannot find the scan part of this csvpath: {data}")
        elif i == len(data) - 1:
            raise InputException(
                f"The scan part of this csvpath cannot be last: {data}"
            )

        scan = data[0 : i + 1]
        scan = scan.strip()

        ndata = data[i + 1 :]
        ndata = ndata.strip()

        if ndata == "":
            raise InputException(f"There must be a match part of this csvpath: {data}")

        if ndata[0] != "[":
            raise InputException(f"Cannot find the match part of this csvpath: {data}")
        if ndata[len(ndata) - 1] != "]":
            raise InputException(f"The match part of this csvpath is incorrect: {data}")
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
            identity: {self.identity}
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
    def collect(self, csvpath: str = None, *, nexts: int = -1) -> List[List[Any]]:
        """Runs the csvpath forward and returns the matching lines seen as
        a list of lists"""
        if self.scanner is None and csvpath is not None:
            self.parse(csvpath)
        if nexts < -1:
            raise ProcessingException(
                "Input must be >= -1. -1 means collect to the end of the file."
            )
        self.collecting = True
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

    def fast_forward(self, csvpath=None) -> None:
        """Runs the path for all rows of the file. Variables are collected
        and side effects like print happen. No lines are collected.
        """
        if self.scanner is None and csvpath is not None:
            self.parse(csvpath)
        for _ in self.next():
            pass

    def next(self, csvpath=None):
        """Iterates over the lines in the CSV file returning those that match
        the csvpath. collect() and fast_forward() call next() behind the scenes.
        """
        if self.scanner is None and csvpath is not None:
            self.parse(csvpath)
        start = time.time()
        if self.run_mode is True:
            for line in self._next_line():
                b = self._consider_line(line)
                if b:
                    line = self.limit_collection(line)
                    if line is None:
                        msg = "Line cannot be None"
                        self.logger.error(msg)
                        raise MatchException(msg)
                    if len(line) == 0:
                        msg = "Line cannot be len() == 0"
                        self.logger.error(msg)
                        raise MatchException(msg)
                    yield line
                elif self.collecting and self.unmatched_available:
                    if self.unmatched is None:
                        self.unmatched = []
                    line = self.limit_collection(line)
                    # we aren't None and 0 checking as above. needed?
                    self.unmatched.append(line)
                if self.stopped:
                    self.logger.info(
                        "CsvPath has been stopped at line %s",
                        self.line_monitor.physical_line_number,
                    )
                    break
        else:
            self.logger.warning(
                "Csvpath identified as {self.identity} is disabled by run-mode:no-run"
            )
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
        # but when would it happen? shouldn't we just let Python's exception
        # handle it should it really occur?
        #
        if self.scanner.filename is None:
            raise FileException("There is no filename")
        reader = DataFileReader(
            self.scanner.filename, delimiter=self.delimiter, quotechar=self.quotechar
        )
        for line in reader.next():
            self.track_line(line=line)
            yield line
        self.finalize()

    """
    # potential replacement for method above
    # this is a proposal for having the results of one csvpath feed into another
    # in memory. the goal being to both shape the data chain-of-responsibility-style
    # and also to narrow the data for performance gains.
    #
    # we would need:
    #   - csvpaths.chain_result_data
    #   - named-path added to csvpath metadata early-on
    #
    # caching this here for now. jury is out on if it should be added.
    #
    def _next_line_new(self) -> List[Any]:
        self.logger.info("beginning to scan file: %s", self.scanner.filename)
        if self.csvpath and self.csvpaths.chain_result_data:
            rs = csvpath.result_manager.get_named_results(self.metadata["named-paths"])
            for line in rs[len(rs)-1].lines:
                yield line
        elif:
            with open(self.scanner.filename, "r", encoding="utf-8") as file:
                reader = csv.reader(
                    file, delimiter=self.delimiter, quotechar=self.quotechar
                )
                for line in reader:
                    self.track_line(line=line)
                    yield line
        self.finalize()
    """

    def finalize(self) -> None:
        """clears caches, etc. this is an internal method, but not _ because
        it is part of the lifecycle and we might find a reason to call it
        from higher up.
        """
        # this method can run multiple times w/np, but that
        # shouldn't happen anyway.
        self._freeze_path = True
        if self.matcher:
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
        if self.line_monitor.physical_line_number == 0:
            self._run_started_at = datetime.now()

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
            if self.advance_count > 0:
                self.advance_count -= 1
                matches = False
                self.logger.debug(
                    "Advancing one line with {self.advance_count} more skips to go"
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
            #
            # if we are done scanning we can stop
            #
            if self.scanner.is_last(self.line_monitor.physical_line_number):
                self.stop()
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
        """if the match count has already been raised earlier in the matching
        process than the caller we don't raise it; otherwise, we raise."""
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
            if k is None or k >= len(line):
                raise InputException(
                    f"[{self.identity}] Line {self.line_monitor.physical_line_number}: unknown header name: {k}"
                )
            else:
                ls.append(line[k])
        return ls

    def advance(self, ff: int = -1) -> None:
        """Advances the iteration by ff rows. The rows will be seen but not matched."""
        if ff is None:
            raise InputException("Input to advance must not be None")
        if self.line_monitor.physical_end_line_number is None:
            raise ProcessingException(
                "The last line number must be known (physical_end_line_number)"
            )
        if ff == -1:
            a = self.advance_count
            a = (
                self.line_monitor.physical_end_line_number
                - self.line_monitor.physical_line_number
                - a
            )
            self.advance_count = a
        else:
            self.advance_count += ff
        self.advance_count = min(
            self.advance_count, self.line_monitor.physical_end_line_number
        )

    def get_total_lines(self) -> int:  # pylint: disable=C0116
        if (
            self.line_monitor.physical_end_line_number is None
            or self.line_monitor.physical_end_line_number == 0
        ):
            self.get_total_lines_and_headers()
        return self.line_monitor.physical_end_line_number

    def get_total_lines_and_headers(self) -> int:  # pylint: disable=C0116
        if not self.scanner or not self.scanner.filename:
            self.logger.error(
                f"Csvpath identified as {self.identity} has no filename. Since that can happen during error handling an exception won't be raised."
            )
            return -1
        if self.csvpaths:
            self.line_monitor = self.csvpaths.file_manager.get_new_line_monitor(
                self.scanner.filename
            )
            self.headers = self.csvpaths.file_manager.get_original_headers(
                self.scanner.filename
            )
        else:
            lc = LineCounter(self)
            lm, headers = lc.get_lines_and_headers(self.scanner.filename)
            self.line_monitor = lm
            self.headers = headers

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
            self.matcher.AND = self._AND
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
