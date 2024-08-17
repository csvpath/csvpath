from typing import Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ErrorPolicy(Enum):
    STOP = "stop"
    FAIL_AND_STOP = "fail_and_stop"
    FAIL_AND_CONTINUE = "fail_and_continue"
    CONTINUE = "continue"


@dataclass
class Error:
    line: int
    match: int
    scan: int
    error: Exception
    message: str
    json: str
    datum: Any
    filename: str
    at: datetime
