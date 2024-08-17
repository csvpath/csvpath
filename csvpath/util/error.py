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
