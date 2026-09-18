from typing import Any, NewType
from abc import ABC, abstractmethod

# types for clarity
Reference = NewType("Reference", str)


#
# Runner marks a start at refactoring CsvPaths to make it
# more modular. as that process starts, Runners are going
# to access CsvPaths private (`_`) methods as if they
# had privledged access.
#
class Runner(ABC):
    DYNAMIC = ":dynamic"

    JSON = "json"
    JSONL = "jsonl"
    LIST_OF_JSON = "listof"
    DATA_FRAME = "dataframe"

    def __init__(self, csvpaths) -> None:
        self._csvpaths = csvpaths

    @property
    def csvpaths(self) -> None:
        return self._csvpaths

    @abstractmethod
    def run(self) -> Reference | list[Reference]: ...

    def not_none(self, value: Any, msg: str) -> None:
        if msg is None:
            raise ValueError("Cannot validate param without an error msg")
        if value is None:
            raise ValueError(msg)

    def not_empty(self, value: Any, msg: str) -> None:
        if msg is None:
            raise ValueError("Cannot validate param without an error msg")
        if not isinstance(value, (str, dict, list, tuple)):
            raise ValueError("Cannot evaluate emptiness")
        if str(value).strip() == "":
            raise ValueError(msg)
        if len(value) == 0:
            raise ValueError(msg)

    def not_shape(self, value: str) -> None:
        if value is None:
            raise ValueError("Shape cannot be None")
        if not isinstance(value, str):
            raise ValueError("Shape must be a string")
        if value not in [self.JSON, self.JSONL, self.LIST_OF_JSON]:
            raise ValueError(
                f"Shape must be one of ({self.JSON},{self.JSONL},{self.LIST_OF_JSON})"
            )
