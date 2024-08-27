from typing import Any, List
from datetime import datetime
from enum import Enum
from csvpath.util.config import OnError
from csvpath import ConfigurationException


class Error:
    def __init__(self):
        self.line_count: int = -1
        self.match_count: int = -1
        self.scan_count: int = -1
        self.error: Exception = None
        self.source: Any = None
        self.message: str = None
        self.json: str = None
        self.datum: Any = None
        self.filename: str = None
        self.at: datetime = datetime.now()

    def __str__(self) -> str:
        return f"""Error
exception: {self.error if self.error else ""}
exception class: {self.error.__class__ if self.error else ""}
filename: {self.filename if self.filename else ""}
datetime: {self.at}
message: {self.message if self.message else ""}
line: {self.line_count if self.line_count is not None else ""}
scan: {self.scan_count if self.scan_count else ""}
match: {self.match_count if self.match_count else ""}
datum: {self.datum if self.datum else ""}
json: {self.json if self.json else ""}
"""


class ErrorHandler:
    def __init__(self, *, csvpath=None, csvpaths=None, error_collector=None):
        self._csvpath = csvpath
        self._csvpaths = csvpaths
        self._error_collector = (
            error_collector if error_collector is not None else csvpath
        )
        if self._error_collector is None:
            raise ConfigurationException(
                "A CsvPathErrorCollector collector must be available. CsvPath or CsvPathResult."
            )

    def handle_error(self, ex: Exception) -> Error:
        if self._csvpath is None and self._csvpaths is None:
            raise ConfigurationException(
                "A CsvPath and/or CsvPaths instance must be available"
            )
        error = self.build(ex)
        if self._csvpath:
            self._handle_if(
                collector=self._error_collector,
                policy=self._csvpath.config.CSVPATH_ON_ERROR,
                error=error,
            )
        if self._csvpaths:
            self._handle_if(
                collector=self._error_collector,
                policy=self._csvpaths.config.CSVPATHS_ON_ERROR,
                error=error,
            )

    def _handle_if(self, *, collector, policy: List[str], error: Error) -> None:
        print(f"Error._handle_if: policy: {policy}")

        if OnError.QUIET.value not in policy:
            #
            # this doesn't go to standard out so it's already "quiet".
            # do we really want to let people rely on just the collected
            # errors? what would be the advantage? Otoh, this will drop
            # a lot of text into the log. maybe just print a single
            # line?
            #
            if self._csvpath:
                self._csvpath.logger.error(f"{error}")
            else:
                self._csvpaths.logger.error(f"{error}")
        else:
            if self._csvpath:
                self._csvpath.logger.error(f"{error.message}")
            else:
                self._csvpaths.logger.error(f"{error.exception_class}: {error.message}")

        if OnError.STOP.value in policy:
            self._csvpath.stopped = True
        if OnError.COLLECT.value in policy:
            collector.collect_error(error)
        if OnError.FAIL.value in policy:
            self._csvpath.is_valid = False
        if OnError.RAISE.value in policy:
            raise error.error

    def build(self, ex: Exception) -> Error:
        error = Error()
        error.error = ex
        error.at = datetime.now()
        if self._csvpath:
            error.line_count = self._csvpath.line_number if self._csvpath else -1
            error.match_count = self._csvpath.match_count if self._csvpath else -1
            error.scan_count = self._csvpath.scan_count if self._csvpath else -1
            error.filename = (
                self._csvpath.scanner.filename
                if self._csvpath and self._csvpath.scanner
                else None
            )
        if hasattr(ex, "json"):
            error.json = ex.json
        elif hasattr(ex, "datum"):
            error.datum = ex.datum
        elif hasattr(ex, "trace"):
            error.message = ex.trace
        elif hasattr(ex, "source"):
            error.source = ex.source
        return error
