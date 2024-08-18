from typing import Any
from datetime import datetime
from enum import Enum


class ErrorPolicy(Enum):
    STOP = "stop"
    FAIL_AND_STOP = "fail_and_stop"
    FAIL_AND_CONTINUE = "fail_and_continue"
    CONTINUE = "continue"


class Error:
    def __init__(self):
        self.line_count: int = -1
        self.match_count: int = -1
        self.scan_count: int = -1
        self.error: Exception = None
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
