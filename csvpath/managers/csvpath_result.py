# pylint: disable=C0114
from typing import Dict, List, Any
from abc import ABC, abstractmethod
from ..util.error import Error
from ..util.printer import Printer
from .. import CsvPath


class CsvPathErrorCollector(ABC):
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


class CsvPathResult(CsvPathErrorCollector, Printer):  # pylint: disable=R0902
    """This class handles the results for a single CsvPath in the
    context of a CsvPaths run that may apply any number of CsvPath
    instances against the same file.
    """

    # re: R0902: disagree that there's too many attributes in this case

    def __init__(
        self,
        *,
        lines: List[List[Any]] = None,
        csvpath: CsvPath,
        file_name: str,
        paths_name: str,
    ):
        self._lines: List[List[Any]] = None
        self._csvpath = None
        self._paths_name = paths_name
        self._file_name = file_name
        self._errors = []
        self._printouts = {}
        self._print_count = 0
        self._last_line = None
        # use the properties so error_collector, etc. is set correctly
        self.csvpath = csvpath
        self.lines = lines

    @property
    def variables(self) -> Dict[str, Any]:  # pylint: disable=C0116
        return self.csvpath.variables

    @property
    def all_variables(self) -> Dict[str, Any]:  # pylint: disable=C0116
        return self.csvpath.csvpaths.results_manager.get_variables(self.paths_name)

    @property
    def paths_name(self) -> str:  # pylint: disable=C0116
        return self._paths_name

    @paths_name.setter
    def paths_name(self, paths_name: str) -> None:
        self._paths_name = paths_name

    @property
    def file_name(self) -> str:  # pylint: disable=C0116
        return self._file_name

    @file_name.setter
    def file_name(self, file_name: str) -> None:
        self._file_name = file_name

    @property
    def lines(self) -> List[List[Any]]:  # pylint: disable=C0116
        return self._lines

    @lines.setter
    def lines(self, ls: List[List[Any]]) -> None:
        self._lines = ls

    @property
    def csvpath(self) -> CsvPath:  # pylint: disable=C0116
        return self._csvpath

    @csvpath.setter
    def csvpath(self, path: CsvPath) -> None:
        path.error_collector = self
        path.add_printer(self)
        self._csvpath = path

    @property
    def errors(self) -> List[Error]:  # pylint: disable=C0116
        return self._errors

    def errors_count(self) -> int:  # pylint: disable=C0116
        return len(self._errors) if self._errors else 0

    def collect_error(self, error: Error) -> None:  # pylint: disable=C0116
        self._errors.append(error)

    def has_errors(self) -> bool:  # pylint: disable=C0116
        return len(self.errors) > 0

    def is_valid(self) -> bool:  # pylint: disable=C0116
        if self._csvpath:
            return self._csvpath.is_valid
        return False

    @property
    def printouts(self) -> List[str]:
        """this method returns the default printouts. use get_printout_by_name
        for specific printouts"""
        if self._printouts is None:
            self._printouts = []
        return self._printouts["default"] if "default" in self._printouts else []

    def get_printout_by_name(self, name: str) -> List[str]:  # pylint: disable=C0116
        if self._printouts is None:
            self._printouts = []
        return self._printouts[name] if name in self._printouts else []

    def has_printouts(self) -> bool:  # pylint: disable=C0116
        return len(self._printouts) > 0 if self._printouts else False

    @property
    def lines_printed(self) -> int:  # pylint: disable=C0116
        return self._print_count

    def print(self, string: str) -> None:  # pylint: disable=C0116
        self.print_to("default", string)

    def print_to(self, name: str, string: str) -> None:  # pylint: disable=C0116
        self._print_count += 1
        if name not in self._printouts:
            self._printouts[name] = []
        self._printouts[name].append(string)
        self._last_line = string

    @property
    def last_line(self):  # pylint: disable=C0116
        return self._last_line

    def dump_printing(self) -> None:  # pylint: disable=C0116
        for name in self._printouts:
            for line in self._printouts[name]:
                print(line)
            print("")

    def print_statements_count(self) -> int:  # pylint: disable=C0116
        i = 0
        for name in self._printouts:
            i += len(self._printouts[name]) if self._printouts[name] else 0
        return i

    def __str__(self) -> str:
        return f"""CsvPathResult
                   file:{self.csvpath.scanner.filename if self.csvpath.scanner else None};
                   name of paths:{self.paths_name};
                   name of file:{self.file_name};
                   valid:{self.csvpath.is_valid};
                   stopped:{self.csvpath.stopped};
                   last line processed:{self.csvpath.line_monitor.physical_line_number};
                   total file lines:{self.csvpath.line_monitor.physical_end_line_number};
                   matches:{self.csvpath.match_count};
                   lines captured:{len(self.lines) if self.lines else 0};
                   print statements:{self.print_statements_count()};
                   errors:{len(self.errors)}"""
