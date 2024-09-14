from typing import Any, List
from datetime import datetime
from enum import Enum
import traceback
from csvpath.util.config import OnError, CsvPathConfig
from .exceptions import InputException
from .log_utility import LogException


class ErrorHandlingException(Exception):
    pass


class Error:
    """ErrorHandler will build errors from exceptions. creating errors is
    not something CsvPath users should need to do
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
        self.at: datetime = datetime.now()

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


class ErrorHandler:
    """creates errors given an exception and uses the csvpaths's or
    csvpath's error policy to handle them. you must provide either
    a CsvPaths or a CsvPath and an ErrorCollector. ErrorCollectors
    are either a CsvPath instance (in which case, just pass the
    instance as both csvpaths=inst and error_collector=inst) or a
    CsvPathResult.
    """

    def __init__(self, *, csvpaths=None, csvpath=None, error_collector):
        self._csvpath = csvpath
        self._csvpaths = csvpaths
        self._error_collector = error_collector
        if self._error_collector is None:
            raise ErrorHandlingException(
                "A CsvPathErrorCollector collector must be available"
            )
        self._logger = None

    @property
    def logger(self):
        if self._logger is None:
            self._logger = (
                self._csvpaths.logger
                if self._csvpaths is not None
                else self._csvpath.logger
            )
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
            self.logger.error(f"Quiet class: {error.exception_class}")
            self.logger.error(f"Quiet file: {error.filename}")
            self.logger.error(f"Quiet line_count: {error.line_count}")
        else:
            self.logger.error(f"{error}")
        if OnError.STOP.value in policy:
            if self._csvpath:
                self._csvpath.stopped = True
        if OnError.COLLECT.value in policy:
            self._error_collector.collect_error(error)
        if OnError.FAIL.value in policy:
            if self._csvpath:
                self._csvpath.is_valid = False
        if OnError.RAISE.value in policy:
            raise error.error

    def build(self, ex: Exception) -> Error:
        error = Error()
        error.error = ex
        error.exception_class = ex.__class__.__name__
        error.at = datetime.now()
        if self._csvpath:
            error.line_count = (
                self._csvpath.line_monitor.physical_line_number if self._csvpath else -1
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
