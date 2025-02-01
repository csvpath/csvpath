from abc import ABC, abstractmethod
from typing import Any, List
from .error import Error
from ..listener import Listener
from ..metadata import Metadata

#
# this class is used by CsvPaths, CsvPath, and Result in this way:
#  - CsvPaths, for any errors that happen during setup, tear-down
#    and/or manager activities
#  - Result, for any errors that bubble up from a CsvPath that is
#    managed by a CsvPaths
#  - CsvPath, for any errors that happen when there is not a
#    CsvPaths to handle them.
#
# if an error occurs during a run, the error goes to the CsvPath.
# if there is a CsvPaths, the CsvPath will be feeding back to a
# Result. The Result will be streaming to a file. If the error
# occurs at another time, the error goes to the CsvPaths.
#


class ErrorCollector(ABC):
    """error collectors collect errors primarily from expressions,
    but also matcher, scanner, and elsewhere."""

    @property
    @abstractmethod
    def errors(self) -> List[Error]:  # pylint: disable=C0116
        ...

    @abstractmethod
    def collect_error(self, error: Error) -> None:  # pylint: disable=C0116
        ...

    @abstractmethod
    def has_errors(self) -> bool:  # pylint: disable=C0116
        ...


class Collector(ErrorCollector, Listener):
    def __init__(self) -> None:
        ErrorCollector.__init__(self)
        Listener.__init__(self)
        self.errors = []

    def metadata_update(self, mdata: Metadata) -> None:
        if isinstance(mdata, Error):
            self.collect_error(mdata)

    def errors(self) -> List[Error]:  # pylint: disable=C0116
        return self.errors

    @abstractmethod
    def collect_error(self, error: Error) -> None:  # pylint: disable=C0116
        self.errors.append(error)

    @abstractmethod
    def has_errors(self) -> bool:  # pylint: disable=C0116
        return len(self.errors) > 0
