from typing import Any, List
from datetime import datetime
from enum import Enum
import traceback
from csvpath.util.config import OnError, CsvPathConfig
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
        string = f"""Error
exception: {self.error if self.error else ""}
exception class: {self.error.__class__ if self.error else ""}
filename: {self.filename if self.filename else ""}
datetime: {self.at}"""
        if self.message:
            string = f"""{string}
message: self.message"""
        string = f"""{string}
line: {self.line_count if self.line_count is not None else ""}
scan: {self.scan_count if self.scan_count else ""}
match: {self.match_count if self.match_count else ""}
datum: {self.datum if self.datum else ""}
json: {self.json if self.json else ""}
"""


class ErrorHandler:
    def __init__(self, *, csvpath=None, logger, error_collector, component: str):
        self._csvpath = csvpath
        self.logger = logger
        if self.logger is None:
            raise ConfigurationException("Logger cannot be None")
        self.component = component
        if self.component not in ["csvpath", "csvpaths"]:
            raise ConfigurationException(f"Unknown component: {self.component}")
        self._error_collector = error_collector
        if self._error_collector is None:
            raise ConfigurationException(
                "A CsvPathErrorCollector collector must be available"
            )

    def handle_error(self, ex: Exception) -> Error:
        error = self.build(ex)
        if self._csvpath:
            policy = self._csvpath.config.CSVPATH_ON_ERROR
        else:
            policy = CsvPathConfig().CSVPATHS_ON_ERROR
        self._handle_if(
            policy=policy,
            error=error,
        )

    def _handle_if(self, *, policy: List[str], error: Error) -> None:
        self.logger.debug(
            f"Handling an error with {self._error_collector.__class__} and policy: {policy}"
        )
        try:
            if OnError.QUIET.value in policy:
                self.logger.error(f"{error}")
            else:
                self.logger.error(f"Error: {error}")
            if OnError.STOP.value in policy:
                if self._csvpath:
                    self._csvpath.stopped = True
            if OnError.COLLECT.value in policy:
                self._error_collector.collect_error(error)
            if OnError.FAIL.value in policy:
                if self._csvpath:
                    self._csvpath.is_valid = False
        except Exception:
            print(f"Error during handling error: {traceback.format_exc()}")
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
        if hasattr(ex, "json"):
            error.json = ex.json
        if hasattr(ex, "datum") and error.datum != "":
            error.datum = ex.datum
        if hasattr(ex, "trace"):
            error.message = ex.trace
        if hasattr(ex, "source"):
            error.source = ex.source
        return error
