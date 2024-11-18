from abc import ABC, abstractmethod
from typing import Any, List
from datetime import datetime
from enum import Enum
import traceback
from csvpath.util.config import OnError
from .exceptions import InputException
from .log_utility import LogException
from ..matching.util.exceptions import MatchException
from ..matching.util.exceptions import ChildrenValidationException


class ErrorHandlingException(Exception):
    pass


class ErrorCommsManager:
    """this class determines how errors should be handled. basically there
    are two types of errors:
    1. built-in validation errors that come from the Args class in two
       passes: pre-run match component tree checking and line by line
       expected values validation
    2. rules errors where match components raise due to circumstances
       having to do with the rules they were set up to implement. e.g.
       an end() that is given a -1 will pass it's Args validation
       because Args only looks at the type of a value, not the value
       itself, but end() takes a positive int so it raises an exception
    the error policy in config/config.ini (or whereever your config is)
    is the baseline. however, every csvpath can override the config
    for some of the error handling using a comment with the metadata
    field args-validation-mode. (soon to be validation-mode). config
    has two setting values not tracked in metadata: quiet and log.
    """

    def __init__(self, csvpath=None, csvpaths=None) -> None:
        self._csvpath = csvpath
        self._policy = None
        if csvpath:
            self._policy = csvpath.config.csvpath_errors_policy
        elif csvpaths:
            self._policy = csvpaths.config.csvpaths_errors_policy
        else:
            raise ErrorHandlingException("Must have a CsvPath or CsvPaths instance")

    def do_i_raise(self) -> bool:
        if self._csvpath and self._csvpath.raise_validation_errors is not None:
            return self._csvpath._raise_validation_errors
        return OnError.RAISE.value in self._policy

    def do_i_print(self) -> bool:
        if self._csvpath and self._csvpath.print_validation_errors is not None:
            return self._csvpath._print_validation_errors
        return OnError.PRINT.value in self._policy

    def do_i_stop(self) -> bool:
        if self._csvpath and self._csvpath.stop_on_validation_errors is not None:
            return self._csvpath._stop_on_validation_errors
        return OnError.STOP.value in self._policy

    def do_i_fail(self) -> bool:
        if self._csvpath and self._csvpath.fail_on_validation_errors is not None:
            return self._csvpath._fail_on_validation_errors
        return OnError.FAIL.value in self._policy


class Error:
    """ErrorHandler builds errors from exceptions. CsvPath users shouldn't
    need to construct errors themselves.
    """

    def __init__(self):
        self.line_count: int = -1
        self.match_count: int = -1
        self.scan_count: int = -1
        self.error: Exception = None
        self.source: Any = None
        self.message: str = None
        self.trace: str = None
        self.json: str = None
        self.datum: Any = None
        self.filename: str = None
        self.at: datetime.now()

    def to_json(self) -> dict:
        ret = {
            "line_count": self.line_count,
            "match_count": self.match_count,
            "scan_count": self.scan_count,
            "error": f"{self.error}",
            "source": f"{self.source}",
            "message": self.message,
            "trace": self.trace,
            "json": self.json,
            "datum": self.datum,
            "filename": self.filename,
            "at": f"{self.at}",
        }
        return ret

    def __str__(self) -> str:
        string = f"""Error
exception: {self.error if self.error else ""}
exception class: {self.error.__class__ if self.error else ""}
filename: {self.filename if self.filename else ""}
datetime: {self.at}"""
        if self.message:
            string = f"""{string}
message: {self.message}"""
        if self.trace:
            string = f"""{string}
trace: {self.trace}"""
        string = f"""{string}
line: {self.line_count if self.line_count is not None else ""}
scan: {self.scan_count if self.scan_count else ""}
match: {self.match_count if self.match_count else ""}
datum: {self.datum if self.datum else ""}
json: {self.json if self.json else ""}
"""
        return string


class ErrorCollector(ABC):
    """error collectors collect errors primarily from expressions,
    but also matcher, scanner, and elsewhere."""

    @property
    @abstractmethod
    def errors(self) -> List[Error]:  # pylint: disable=C0116
        pass

    @abstractmethod
    def collect_error(self, error: Error) -> None:  # pylint: disable=C0116
        pass

    @abstractmethod
    def has_errors(self) -> bool:  # pylint: disable=C0116
        pass


class ErrorHandler:
    """creates errors given an exception and uses the csvpaths's or
    csvpath's error policy to handle them. you must provide either
    a CsvPaths or a CsvPath and an ErrorCollector. ErrorCollectors
    are either a CsvPath instance (in which case, just pass the
    instance as both csvpaths=inst and error_collector=inst) or a
    Result.
    """

    def __init__(self, *, csvpaths=None, csvpath=None, error_collector=None):
        self._csvpath = csvpath
        self._csvpaths = csvpaths
        self._error_collector = error_collector
        if self._error_collector is None:
            if self._csvpaths:
                self._error_collector = self._csvpaths
            elif self._csvpath:
                self._error_collector = self._csvpath
            else:
                raise ErrorHandlingException(
                    "A CsvPathErrorCollector collector must be available"
                )
        self._ecm = ErrorCommsManager(csvpath=csvpath, csvpaths=csvpaths)
        self._logger = None

    @property
    def logger(self):
        if self._logger is None:
            if self._csvpaths:
                self._logger = self._csvpaths.logger
            elif self._csvpath:
                self._logger = self._csvpath.logger
            else:
                raise ErrorHandlingException("No logger available")
        return self._logger

    def handle_error(self, ex: Exception) -> Error:
        error = self.build(ex)
        if self._csvpath:
            policy = self._csvpath.config.csvpath_errors_policy
        elif self._csvpaths:
            policy = self._csvpaths.config.csvpaths_errors_policy
        else:
            raise ErrorHandlingException("Csvpath or CsvPaths must be present")
        self._handle_if(
            policy=policy,
            error=error,
        )

    def _handle_if(self, *, policy: List[str], error: Error) -> None:
        self.logger.debug(
            f"Handling an error with {self._error_collector.__class__} and policy: {policy}"
        )
        if error is None:
            raise InputException("Error handler cannot handle a None error")
        if OnError.QUIET.value in policy:
            self.logger.error(f"Quiet error: {error.exception}")
            self.logger.error(f"Quiet error class: {error.exception_class}")
            self.logger.error(f"Quiet error file: {error.filename}")
            self.logger.error(f"Quiet error line_count: {error.line_count}")
        else:
            self.logger.error(f"{error}")
        if self._ecm.do_i_stop() is True:
            if self._csvpath:
                self._csvpath.stopped = True
        if OnError.COLLECT.value in policy:
            self._error_collector.collect_error(error)
        if self._ecm.do_i_fail() is True:
            if self._csvpath:
                self._csvpath.is_valid = False
        if self._ecm.do_i_print() is True:
            #
            # we give the comments settings a vote. comments settings
            # give people a way to set the noise level on a csvpath by
            # csvpath basis when working within a CsvPaths instance.
            # if we didn't provide this the error policy would be one
            # size fits all. given how important validation output is
            # we want to be more flexible.
            #
            if self._csvpath:
                self._csvpath.print(f"{error.error}")
            else:
                self._csvpaths.logger.warning(
                    "attempted to print an error to system out, but CsvPaths do not print errors. This was the error: %s",
                    error.error,
                )
        if self._ecm.do_i_raise() is True:
            raise MatchException(
                f"Exception raised by error policy {policy}"
            ) from error.error

    def build(self, ex: Exception) -> Error:
        error = Error()
        error.error = ex
        error.exception_class = ex.__class__.__name__
        error.at = datetime.now()
        if self._csvpath:
            if self._csvpath.line_monitor:
                error.line_count = (
                    self._csvpath.line_monitor.physical_line_number
                    if self._csvpath
                    else -1
                )
            error.match_count = self._csvpath.match_count if self._csvpath else -1
            error.scan_count = self._csvpath.scan_count if self._csvpath else -1
            error.filename = (
                self._csvpath.scanner.filename
                if self._csvpath and self._csvpath.scanner
                else None
            )
            error.match = self._csvpath.match
        else:
            error.line_count = "unknown"
            error.match = "unknown"
        if hasattr(ex, "json"):
            error.json = ex.json
        if hasattr(ex, "datum") and error.datum != "":
            error.datum = ex.datum
        if hasattr(ex, "message"):
            error.message = ex.message
        if hasattr(ex, "trace"):
            error.trace = ex.trace
        if hasattr(ex, "source"):
            error.source = ex.source
        return error
