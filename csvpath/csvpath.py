""" CsvPath is the main class for the library. most of the magic
    happens either here or in individual functions. """  # pylint: disable=C0302

import time
import os
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any
from collections.abc import Iterator
from abc import ABC, abstractmethod
from .util.config import Config
from .util.line_monitor import LineMonitor
from .util.log_utility import LogUtility
from .util.printer import Printer
from .util.file_readers import DataFileReader
from .util.line_spooler import LineSpooler, ListLineSpooler
from .modes.mode_controller import ModeController
from .matching.matcher import Matcher
from .scanning.scanner import Scanner
from .util.metadata_parser import MetadataParser
from .managers.errors.error import Error
from .managers.errors.error_comms import ErrorCommunications
from .managers.errors.error_manager import ErrorManager
from .managers.metadata import Metadata
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
from .managers.errors.error_collector import ErrorCollector


class CsvPath(ErrorCollector, Printer):  # pylint: disable=R0902, R0904
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
        # config=None,
        error_manager=None,
    ):
        # re: R0913: all reasonable pass-ins with sensible defaults
        #
        # the config.ini file loaded as a ConfigParser instance
        #

        """
        #
        # passing in the config actually nets us nothing but a little unnecessary complexity that we don't use.
        #
        # we want to be able to override config.ini specifically for
        # this instance, if needed; however, we do want to be able
        # to pass in a config object that has been configured in some
        # way.
        """
        self._config = Config()  # config
        self.scanner = None
        """ @private """
        self.matcher = None
        """ @private """
        #
        # a parent CsvPaths may manage a CsvPath instance. if so, it will enable
        # the use of named files and named paths, print capture, error handling,
        # results collection, reference handling, etc. if a CsvPaths is not present
        # the CsvPath instance is responsible for all its own upkeep and does not
        # have some of those capabilities.
        #
        self.csvpaths = csvpaths
        """ @private """
        #
        # there are two logger components one for CsvPath and one for CsvPaths.
        # the default levels are set in config.ini. to change the levels pass LogUtility
        # your component instance and the logging level. e.g.:
        # LogUtility.logger(csvpath, "debug")
        #
        self.logger = LogUtility.logger(self)
        """ @private """
        self.logger.info("initialized CsvPath")
        #
        # if we don't have a csvpaths these will both be None
        #
        self.named_paths_name = None
        """ @private """
        self.named_file_name = None
        """ @private """
        #
        # all errors come to our manager if they occur during matching. we use
        # the CsvPaths manager if possible. Otherwise, we just make our own that
        # only knows how to collect errors, not distribute them.
        #
        self.ecoms = ErrorCommunications(csvpath=self)
        """ @private """
        self.error_manager = ErrorManager(csvpath=self)
        if csvpaths is not None:
            self.error_manager.add_internal_listener(csvpaths.error_manager)
        #
        # modes are set in external comments
        #
        self.modes = ModeController(self)
        """ @private """
        #
        # captures the number of lines up front and tracks line stats as the
        # run progresses
        #
        self._line_monitor = None
        #
        # the scanning part of the csvpath. e.g. $test.csv[*]
        #
        self.scan = None
        """ @private """
        #
        # the matching part of the csvpath. e.g. [yes()]
        #
        self.match = None
        """ @private """
        #
        # when True the lines that do not match are returned from next()
        # and collect(). this effectively switches CsvPath from being an
        # create an OR expression in this case. in the default, we say:
        #     are all of these things true?
        # but when collect_when_not_matched is True we ask:
        #     are any of these things not true?
        #
        # self._when_not_matched = False
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
        # the lines var will hold a reference to a LineSpooler instance during a
        # run, if lines are being collected by the collect() method. if the user
        # is using this CsvPath instance directly the LineSpooler is only there
        # as a proxy to the list of lines being collected -- we don't spool to
        # disk, at least atm.
        #
        self.lines = None
        """ @private """
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
        """ @private """
        self.rows_time = -1
        """ @private """
        self.total_iteration_time = -1
        """ @private """
        #
        # limiting collection means returning fewer headers (values in the
        # line, a.k.a columns) then are available. limiting headers returned
        # can impact named results, reset_headers(), and other considerations.
        #
        self._limit_collection_to = []
        #
        # error collecting is at the CsvPath instance by default. CsvPath
        # instances that are managed by a CsvPaths have their errors collected
        # by their Results as well. Result handles persistence.
        #
        # errors policies are set in config.ini at CsvPath and CsvPaths levels.
        #
        self._errors: List[Error] = []
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
        """ @private """
        if print_default:
            self.printers.append(StdOutPrinter())
        #
        # _function_times_match collects the time a function spends doing its matches()
        #
        self._function_times_match = {}
        #
        # _function_times_value collects the time a function spends doing its to_value()
        #
        self._function_times_value = {}
        self._created_at = datetime.now(timezone.utc)
        self._run_started_at = None
        self._collecting = False
        #
        # holds the unmatched lines when lines are being collected and
        # _unmatched_available is True. it is analogous to the lines returned
        # by collect(), but is the lines not returned by collect().
        #
        self._unmatched = None

    #
    # this method saves and reloads the config. if you don't want that use
    # CsvPath.config.save_to_config().
    #
    def add_to_config(self, section, key, value) -> None:
        """@private"""
        self.config.add_to_config(section=section, key=key, value=value)
        self.config.save_config()
        self.config.reload()

    @property
    def data_from_preceding(self) -> bool:
        """@private"""
        return self.modes.source_mode.value

    @data_from_preceding.setter
    def data_from_preceding(self, dfp: bool) -> None:
        """@private"""
        self.modes.source_mode.value = dfp

    @property
    def unmatched(self) -> list[list[Any]]:
        """@private"""
        return self._unmatched

    @unmatched.setter
    def unmatched(self, lines: list[list[Any]]) -> None:
        """@private"""
        self._unmatched = lines

    @property
    def collecting(self) -> bool:
        """@private"""
        return self._collecting

    @collecting.setter
    def collecting(self, c: bool) -> None:
        """@private"""
        self._collecting = c

    @property
    def unmatched_available(self) -> bool:
        """@private"""
        return self.modes.unmatched_mode.value

    @unmatched_available.setter
    def unmatched_available(self, ua: bool) -> None:
        """@private"""
        self.modes.unmatched_mode.value = ua

    @property
    def created_at(self) -> datetime:
        """@private"""
        return self._created_at

    @property
    def run_started_at(self) -> datetime:
        """@private"""
        return self._run_started_at

    @property
    def will_run(self) -> bool:
        """@private"""
        return self.modes.run_mode.value

    @will_run.setter
    def will_run(self, mode) -> None:
        """@private"""
        self.modes.run_mode.value = mode

    #
    # increases the total accumulated time spent doing c.matches() by t
    #
    def up_function_time_match(self, c, t) -> None:
        """@private"""
        if c not in self.function_times_match:
            self.function_times_match[c] = 0
        st = self.function_times_match[c]
        st += t
        self.function_times_match[c] = st

    @property
    def function_times_match(self) -> int:
        """@private"""
        return self._function_times_match

    #
    # increases the total accumulated time spent doing c.to_value() by t
    #
    def up_function_time_value(self, c, t) -> None:
        """@private"""
        if c not in self.function_times_value:
            self.function_times_value[c] = 0
        st = self.function_times_value[c]
        st += t
        self.function_times_value[c] = st

    @property
    def function_times_value(self) -> int:
        """@private"""
        return self._function_times_value

    def do_i_raise(self) -> bool:
        """@private"""
        return self.ecoms.do_i_raise()

    @property
    def advance_count(self) -> int:  # pragma: no cover
        """@private"""
        return self._advance

    @advance_count.setter
    def advance_count(self, lines: int) -> None:
        """@private"""
        self._advance = lines

    @property
    def headers(self) -> List[str]:
        """@private"""
        if self._headers is None:
            self.get_total_lines_and_headers()
        return self._headers

    @headers.setter
    def headers(self, headers: List[str]) -> None:
        """@private"""
        self._headers = headers

    @property
    def line_monitor(self) -> LineMonitor:
        """@private"""
        if self._line_monitor is None:
            self.get_total_lines_and_headers()
        return self._line_monitor

    @line_monitor.setter
    def line_monitor(self, lm) -> None:
        """@private"""
        self._line_monitor = lm

    @property
    def AND(self) -> bool:  # pylint: disable=C0103
        return self.modes.logic_mode.value

    @AND.setter
    def AND(self, a: bool) -> bool:  # pylint: disable=C0103
        self.modes.logic_mode.value = a

    @property
    def OR(self) -> bool:  # pylint: disable=C0103
        return not self.modes.logic_mode.value

    @OR.setter
    def OR(self, a: bool) -> bool:  # pylint: disable=C0103
        self.modes.logic_mode.value = not a

    @property
    def identity(self) -> str:
        """returns id or name if found in metadata.

        the id or name gets into metadata primarily if found
        in an "external" comment in the csvpath. "external"
        meaning outside the []s. comments are keyword:comment.
        we take id, Id, ID and name, Name, NAME.

        id is preferred over name. E.g. in:
        ~ name: my path description: an example id: this value wins ~
        the id becomes the identity of the instance.

        we prefer in this order: all-lower most, Initial-caps,
        ALL-CAPS least

        the ordering is relied on in Result and possibly
        elsewhere.
        """
        ret = None
        if not self.metadata:
            ret = ""
        if "NAME" in self.metadata:
            ret = self.metadata["NAME"]
        if "Name" in self.metadata:
            ret = self.metadata["Name"]
        if "name" in self.metadata:
            ret = self.metadata["name"]
        if "ID" in self.metadata:
            ret = self.metadata["ID"]
        if "Id" in self.metadata:
            ret = self.metadata["Id"]
        if "id" in self.metadata:
            ret = self.metadata["id"]
        return ret

    @property
    def config(self) -> Config:  # pylint: disable=C0116
        """@private"""
        if not self._config:
            self._config = Config()
        return self._config

    # ==========================
    # Errors
    # <thinking> if we have a csvpaths people should look at the result to find errors
    # but we give access to metadata, vars, etc. from the csvpath, so we should
    # give errors too. that means we need to have our own listener. ultimately we'd
    # just be adding pointers, not dup the original error data.
    #
    def metadata_update(self, mdata: Metadata) -> None:
        """@private"""
        if isinstance(mdata, Error):
            self.collect_error(mdata)

    @property
    def errors(self) -> List[Error]:  # pylint: disable=C0116
        return self._errors

    @property
    def errors_count(self) -> int:  # pylint: disable=C0116
        return len(self.errors)

    def collect_error(self, error: Error) -> None:  # pylint: disable=C0116
        """@private"""
        self.errors.append(error)

    def has_errors(self) -> bool:
        return self.errors_count > 0

    @property
    def stop_on_validation_errors(self) -> bool:
        """@private"""
        return self.modes.validation_mode.stop_on_validation_errors

    @property
    def fail_on_validation_errors(self) -> bool:
        """@private"""
        return self.modes.validation_mode.fail_on_validation_errors

    @property
    def print_validation_errors(self) -> bool:
        """@private"""
        return self.modes.validation_mode.print_validation_errors

    @property
    def log_validation_errors(self) -> bool:
        """@private"""
        return self.modes.validation_mode.log_validation_errors

    @property
    def raise_validation_errors(self) -> bool:
        """@private"""
        return self.modes.validation_mode.raise_validation_errors

    @property
    def match_validation_errors(self) -> bool:
        """@private"""
        return self.modes.validation_mode.match_validation_errors

    @property
    def collect_validation_errors(self) -> bool:
        """@private"""
        return self.modes.validation_mode.collect_validation_errors

    def add_printer(self, printer) -> None:  # pylint: disable=C0116
        """@private"""
        if printer not in self.printers:
            self.printers.append(printer)

    def set_printers(self, printers: List) -> None:  # pylint: disable=C0116
        """@private"""
        self.printers = printers

    @property
    def has_default_printer(self) -> bool:
        """@private"""
        if not self.printers:
            self.printers = []
        for p in self.printers:
            if isinstance(p, StdOutPrinter):
                return True
        return False

    def print(self, string: str) -> None:  # pylint: disable=C0116
        """@private"""
        for p in self.printers:
            p.print(string)

    def print_to(self, name: str, string: str) -> None:
        """@private"""
        for p in self.printers:
            p.print_to(name, string)

    @property
    def last_line(self):
        """@private
        this method only returns the default printer's last_line"""
        if not self.printers or len(self.printers) == 0:
            return None
        return self.printers[0].last_line

    @property
    def lines_printed(self) -> int:
        """@private
        this method only returns the default printer's lines printed"""
        if not self.printers or len(self.printers) == 0:
            return -1
        return self.printers[0].lines_printed

    @property
    def is_frozen(self) -> bool:
        """@private
        True if the instance is matching on its last row only to
        allow last()s to run; in which case, no variable updates
        are allowed, along with other limitations."""
        return self._freeze_path

    @is_frozen.setter
    def is_frozen(self, freeze: bool) -> None:
        """@private"""
        self._freeze_path = freeze

    @property
    def explain(self) -> bool:
        """@private
        when this property is True CsvPath dumps a match explanation
        to INFO. this can be expensive. a 25% performance hit wouldn't
        be unexpected.
        """
        return self.modes.explain_mode.value

    @explain.setter
    def explain(self, yesno: bool) -> None:
        """@private"""
        self.modes.explain_mode.value = yesno

    @property
    def collect_when_not_matched(self) -> bool:
        """@private
        when this property is True CsvPath returns the lines that do not
        match the matchers match components"""
        return self.modes.return_mode.collect_when_not_matched

    @collect_when_not_matched.setter
    def collect_when_not_matched(self, yesno: bool) -> None:
        """@private
        when c ollect_when_not_matched is True we return the lines that failed
        to match, rather than the default behavior of returning the matches.
        """
        self.modes.return_mode.collect_when_not_matched = yesno

    def parse(self, csvpath, disposably=False):
        """@private
        displosably is True when a Matcher is needed for some purpose other than
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
        # exp!
        if disposably is False:
            csvpath = self._update_file_path(csvpath)
        #
        #
        #
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
        """@private"""
        #
        # settings:
        #   - logic-mode: AND | OR
        #   - return-mode: matches | no-matches
        #   - print-mode: default | no-default
        #   - validation-mode: (no-)print | log | (no-)raise | quiet | (no-)match | (no-)stop
        #   - run-mode: no-run | run
        #   - unmatched-mode: no-keep | keep
        #   - source-mode: preceding | origin
        #   - files-mode: all | no-data | no-unmatched | no-printouts | data | unmatched | errors | meta | vars | printouts
        #
        self.modes.update()

    # =====================
    # in principle the modes should come through the mode controller like:
    #      self.modes.transfer_mode.value
    # not wading into that today. low value.
    #
    @property
    def transfer_mode(self) -> str:
        """@private"""
        return self.metadata.get("transfer-mode")

    @property
    def source_mode(self) -> str:
        """@private"""
        return self.metadata.get("source-mode")

    @property
    def error_mode(self) -> str:
        """@private"""
        return self.metadata.get("error-mode")

    @property
    def files_mode(self) -> str:
        """@private"""
        return self.metadata.get("files-mode")

    @property
    def validation_mode(self) -> str:
        """@private"""
        return self.metadata.get("validation-mode")

    @property
    def run_mode(self) -> str:
        """@private"""
        return self.metadata.get("run-mode")

    @property
    def logic_mode(self) -> str:
        """@private"""
        return self.metadata.get("logic-mode")

    @property
    def return_mode(self) -> str:
        """@private"""
        return self.modes.get("return-mode")

    @property
    def explain_mode(self) -> str:
        """@private"""
        return self.metadata.get("explain-mode")

    @property
    def print_mode(self) -> str:
        """@private"""
        return self.metadata.get("print-mode")

    @property
    def unmatched_mode(self) -> str:
        """@private"""
        return self.metadata.get("unmatched-mode")

    # =====================

    @property
    def transfers(self) -> list[tuple[str, str]]:
        """@private"""
        return self.modes.transfer_mode.transfers

    @property
    def all_expected_files(self) -> list[str]:
        """@private"""
        return self.modes.files_mode.all_expected_files

    @all_expected_files.setter
    def all_expected_files(self, efs: list[str]) -> None:
        """@private"""
        self.modes.files_mode.all_expected_files = efs

    def _pick_named_path(self, name, *, specific=None) -> str:
        """@private"""
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
            c = CsvPath(csvpaths=self.csvpaths)
            MetadataParser(c).extract_metadata(instance=c, csvpath=p)
            if c.identity == specific:
                return p
        self.logger.error(
            "Cannot find csvpath identified as %s in named-paths %s", specific, name
        )
        raise ParsingException(f"Cannot find path '{specific}' in named-paths '{name}'")

    def parse_named_path(self, name, *, disposably=False, specific=None):
        """@private
        disposably is True when a Matcher is needed for some purpose other than
        the run we were created to do. could be that a match component wanted a
        parsed csvpath for its own purposes. import() uses this method.
        when True, we create and return the Matcher, but then forget it ever existed.
        also note: the path must have a name or full filename. $[*] is not enough.
        """
        if not self.csvpaths:
            raise CsvPathsException("No CsvPaths object available")

        path = self._pick_named_path(name, specific=specific)
        c = CsvPath(csvpaths=self.csvpaths)
        path = MetadataParser(c).extract_metadata(instance=c, csvpath=path)
        #
        # exp. oddly this seems to be superfluous
        # if disposably is False:
        #    path = c._update_file_path(path)
        #
        dis = c.parse(path, disposably=disposably)
        if disposably is True:
            return dis
        return None

    def _update_file_path(self, data: str):
        """@private
        this method replaces a name (i.e. name in: $name[*[][yes()]) with
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
        #
        # this will blow up frequently when name is an actual path. ie name == path
        # below. since we want file manager to be discriminating we have to catch
        # the error and reset the name
        #
        try:
            path = self.csvpaths.file_manager.get_named_file(name)
        except ValueError:
            path = name
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
        if i == len(data) - 1:
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
        """Csvpaths can flag a CSV file as invalid using the fail() function"""
        return self._is_valid

    @is_valid.setter
    def is_valid(self, tf: bool) -> None:
        self._is_valid = tf

    @property
    def completed(self) -> bool:
        if not self.scanner or not self.line_monitor:
            return False
        if self.scanner.is_last(self.line_monitor.physical_line_number):
            return True
        return False

    @property
    def from_line(self):  # pragma: no cover pylint: disable=C0116
        """@private"""
        if self.scanner is None:
            raise ParsingException("No scanner available. Have you parsed a csvpath?")
        return self.scanner.from_line

    @property
    def to_line(self):  # pragma: no cover pylint: disable=C0116
        """@private"""
        if self.scanner is None:
            raise ParsingException("No scanner available. Have you parsed a csvpath?")
        return self.scanner.to_line

    @property
    def all_lines(self):  # pragma: no cover pylint: disable=C0116
        """@private"""
        if self.scanner is None:
            raise ParsingException("No scanner available. Have you parsed a csvpath?")
        return self.scanner.all_lines

    @property
    def path(self):  # pragma: no cover pylint: disable=C0116
        """@private"""
        if self.scanner is None:
            raise ParsingException("No scanner available. Have you parsed a csvpath?")
        return self.scanner.path

    @property
    def these(self):  # pragma: no cover pylint: disable=C0116
        """@private"""
        if self.scanner is None:
            raise ParsingException("No scanner available. Have you parsed a csvpath?")
        return self.scanner.these

    @property
    def limit_collection_to(self) -> List[int]:
        """@private
        returns the list of headers to collect when a line matches. by default
        this list is empty and all headers are collected.
        """
        return self._limit_collection_to

    @limit_collection_to.setter
    def limit_collection_to(self, indexes: List[int]) -> None:
        """@private"""
        self._limit_collection_to = indexes
        if self._limit_collection_to and self._limit_collection_to != indexes:
            self.logger.info("Limiting headers collected: %s", indexes)

    def stop(self) -> None:
        """@private"""
        self.stopped = True

    #
    #
    # collect(), fast_forward(), and next() are the central methods of CsvPath.
    #
    # remember that since next() is a public method and collect() and fast_forward()
    # rely on it, we have to cut off exceptions at next(). users will not see
    # fast_forward and collect in the stack trace. probably that's not a big deal.
    # if it seems confusing we can work around the problem.
    #
    def collect(
        self, csvpath: str = None, *, nexts: int = -1, lines=None
    ) -> List[List[Any]] | LineSpooler:
        """Runs the csvpath forward and returns the matching lines seen as
        a list of lists. this method does not holds lines locally, not as
        accessible attributes. lines are not kept after the run completes
        and the collected lines are returned.

        the optional lines argument may be an instance of any class that has an append(obj)
        method. if lines is None, a list is returned.
        """
        if self.scanner is None and csvpath is not None:
            self.parse(csvpath)
        if nexts < -1:
            raise ProcessingException(
                "Input must be >= -1. -1 means collect to the end of the file."
            )
        self.collecting = True
        #
        # we're going to use the passed in lines object. if it exists
        # it is a LineSpooler (we presume). we'll associate it with the
        # csvpath temporarily so anyone interested can get it. if it
        # doesn't exist we create a list for the lines var. we create a
        # list LinesSpooler to handle any inquiries during the run we
        # do all our line collecting busness with the local lines var
        # which has an append method regardless of if it is list or
        # LineSpooler. when we're done we break the link with the csvpath
        # and return the local variable. if it is a list it is going to
        # a csvpath user. if it is a LineSpooler it is going to a
        # CsvPaths instance.
        #
        self.lines = lines
        if lines is None:
            lines = []
            self.lines = ListLineSpooler(lines=lines)
        for _ in self.next():
            _ = _[:]
            self.lines.append(_)
            if nexts == -1:
                continue
            if nexts > 1:
                nexts -= 1
            else:
                break
        # we don't want to hold on to data more than needed. but
        # we do want to return data if we're not spooling. the
        # way we do that is to keep the local var available with the
        # list and/or the spooler. the caller needs to be aware of
        # both possibilities, but both offer __len__ and append.
        #
        # we keep the self.lines if it is not a list because that
        # makes it available to the runtime data collector so we can
        # see the line count in the metadata, saving opening a
        # potentially large data.csv to find out how many lines.
        if isinstance(self.lines, list):
            self.lines = None
        return lines

    def fast_forward(self, csvpath=None):
        """Scans to the end of the CSV file. All scanned rows will be
        considered for match and variables and side effects will happen,
        but no rows will be returned or stored. -1 means to the end of
        the file. If you do not pass the csvpath string here you must first
        use the parse method."""
        if self.scanner is None and csvpath is not None:
            self.parse(csvpath)
        for _ in self.next():
            pass
        return self

    #
    # dont_raise is for the use of fast_forward and collect who
    # may want to handle raising errors themselves.
    #
    def next(self, csvpath=None):
        """A generator function that steps through the CSV file returning
        matching rows."""
        try:
            if self.scanner is None and csvpath is not None:
                self.parse(csvpath)
            start = time.time()
            if self.will_run is True:
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
            end = time.time()
            self.total_iteration_time = end - start
            self.logger.info("Run against %s is complete.", self.scanner.filename)
            self.logger.info(
                "Iteration time was %s", round(self.total_iteration_time, 2)
            )
            if (
                self.line_monitor.physical_end_line_count
                and self.line_monitor.physical_end_line_count > 0
            ):
                self.logger.info(
                    "%s per line",
                    round(
                        self.total_iteration_time
                        / self.line_monitor.physical_end_line_count,
                        2,
                    ),
                )
        except Exception as e:
            if not self.ecoms.do_i_quiet():
                self.logger.error(e, exc_info=True)
            if self.ecoms.do_i_raise():
                raise

    def _next_line(self) -> List[Any]:
        """@private"""
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
        #
        # DataFileReader is abstract. instantiating it results in a concrete subclass.
        # pylint doesn't like that just because it doesn't see what we're doing.
        # otoh, is this a bad way to do it? it works fine.
        #
        reader = DataFileReader(  # pylint: disable=E0110
            self.scanner.filename, delimiter=self.delimiter, quotechar=self.quotechar
        )
        for line in reader.next():
            self.track_line(line=line)
            yield line
        self.finalize()

    def finalize(self) -> None:
        """@private
        clears caches, etc. this is an internal method, but not _ because
        it is part of the lifecycle and we might find a reason to call it
        from higher up.
        """
        # this method can run multiple times w/np, but that
        # shouldn't happen anyway.
        self._freeze_path = True
        if self.matcher:
            self.matcher.clear_caches()

    def track_line(self, line) -> None:
        """@private
        csvpaths needs to handle some of the iteration logic, and we don't want
        to lose track of line number monitoring or repeat the code up there,
        so we need this method to give csvpaths a way to tap in.
        """
        last_line = None
        if self.matcher:
            last_line = self.matcher.line
        self.line_monitor.next_line(last_line=last_line, data=line)
        if self.line_monitor.physical_line_number == 0:
            self._run_started_at = datetime.now(timezone.utc)

    def _consider_line(self, line):  # pylint: disable=R0912, R0911
        """@private"""
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
        """@private
        if the match count has already been raised earlier in the matching
        process than the caller we don't raise it; otherwise, we raise."""
        if self._current_match_count == self.match_count:
            self.match_count += 1
        else:
            self.logger.debug("Match count was already raised, so not doing it again")

    def limit_collection(self, line: List[Any]) -> List[Any]:
        """@private
        this method creates a line based on the given line that holds only the headers
        that the csvpath says to collect. headers for collection are indicated using
        the collect() function.
        """
        if len(self.limit_collection_to) == 0:
            return line
        ls = []
        for k in self.limit_collection_to:
            if k is None or k >= len(line):
                #
                # FP change. didn't do do_i_raise and didn't handle w/error mgr
                #
                msg = f"[{self.identity}] Line {self.line_monitor.physical_line_number}: unknown header name: {k} of {self.limit_collection_to} in headers {self.headers}"
                self.error_manager.handle_error(source=self, msg=msg)
                if self.ecoms.do_i_raise():
                    raise InputException(msg)
            ls.append(line[k])
        return ls

    def advance(self, ff: int = -1) -> None:
        """@private
        Advances the iteration by ff rows. The rows will be seen but not matched."""
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
        """@private"""
        if (
            self.line_monitor.physical_end_line_number is None
            or self.line_monitor.physical_end_line_number == 0
        ):
            self.get_total_lines_and_headers()
        return self.line_monitor.physical_end_line_number

    def get_total_lines_and_headers(self) -> None:  # pylint: disable=C0116
        """@private"""
        if not self.scanner or not self.scanner.filename:
            self.logger.error(
                "Csvpath identified as %s has no filename. Since we could be error handling an exception is not raised.",
                self.identity,
            )
            # exp
            return
            # end exp
        #
        # there are times, e.g. when using Lambda, when it may be better to
        # not use a cache. in the case of Lambda the reason is to avoid working
        # around the read-only filesystem.
        #
        use_cache = self.csvpaths is not None
        if use_cache:
            uc = self.csvpaths.config.get(section="cache", name="use_cache")
            use_cache = uc is None or uc.strip().lower() != "no"
        #
        # do we really want to only use cache if we're running a named-paths group?
        # users may want to run one-offs repeatedly, particularly in FP. otoh, we
        # don't have a file_manager and its a big change for probably a small number of
        # bad cases and it can be worked around by simply using a CsvPaths.
        #
        if self.csvpaths and use_cache is True:
            self.line_monitor = self.csvpaths.file_manager.lines_and_headers_cacher.get_new_line_monitor(
                self.scanner.filename
            )
            self.headers = self.csvpaths.file_manager.lines_and_headers_cacher.get_original_headers(
                self.scanner.filename
            )
        else:
            lc = LineCounter(self)
            lm, headers = lc.get_lines_and_headers(self.scanner.filename)
            self.line_monitor = lm
            self.headers = headers

    @property
    def current_scan_count(self) -> int:  # pylint: disable=C0116
        """@private"""
        return self.scan_count

    @property
    def current_match_count(self) -> int:  # pylint: disable=C0116
        """@private"""
        return self.match_count

    def matches(self, line) -> bool:  # pylint: disable=C0116
        """@private"""
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
            self.matcher.AND = self.AND
            #
            # we need to register all the Expressions as error listeners. not
            # sure it matters if we do it here or allow the Matcher to do it.
            # since the Matcher is responsible for its Expressions, has a handle
            # this CsvPath, and through it has the error_manager let's let it
            # register the expressions.
            #
        else:
            self.logger.debug("Resetting and reloading matcher")
            self.matcher.reset()
            self.matcher.line = line
        matched = self.matcher.matches()
        return matched

    def set_variable(self, name: str, *, value: Any, tracking: Any = None) -> None:
        """@private
        sets a variable and the tracking variable as a key within
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
        """@private
        gets a variable by name. uses the tracking value as a key to get
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
        """@private
        returns all the line numbers the scanner will scan during
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
        """@private"""
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
        """@private"""
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
        """@private"""
        collect = []
        if these is None:
            these = []
        for i in self._line_numbers(
            these=these, from_line=from_line, to_line=to_line, all_lines=all_lines
        ):
            collect.append(i)
        return collect

    def header_index(self, name: str) -> int:  # pylint: disable=C0116
        """@private"""
        if not self.headers:
            return None
        for i, n in enumerate(self.headers):
            if n == name:
                return i
        return None
