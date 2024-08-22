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
    def __init__(self, *, csvpath=None, csvpaths=None):
        self._csvpath = csvpath
        self._csvpaths = csvpaths

    def handle_error(self, ex: Exception) -> Error:
        if self._csvpath is None and self._csvpaths is None:
            raise ConfigurationException(
                "A CsvPath and/or CsvPaths instance must be available"
            )
        error = self.build(ex)
        if self._csvpath:
            self._handle_if(self._csvpath.config.CSVPATH_ON_ERROR, error)
        if self._csvpaths:
            self._handle_if(self._csvpath.config.CSVPATHS_ON_ERROR, error)

    def _handle_if(self, policy: List[str], error: Error) -> None:
        print(f"Error._handle_if: policy: {policy}")

        if OnError.QUIET.value not in policy:
            pass
            # do logging
        if OnError.STOP.value in policy:
            self._csvpath.stopped = True
        if OnError.COLLECT.value in policy:
            self._csvpath.collect_error(error)
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
