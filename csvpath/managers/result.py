# pylint: disable=C0114
from typing import Dict, List, Any
from ..util.error import Error, ErrorCollector
from ..util.printer import Printer
from .. import CsvPath


class Result(ErrorCollector, Printer):  # pylint: disable=R0902
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
    def metadata(self) -> Dict[str, Any]:  # pylint: disable=C0116
        return self.csvpath.metadata  # pragma: no cover

    @property
    def variables(self) -> Dict[str, Any]:  # pylint: disable=C0116
        return self.csvpath.variables  # pragma: no cover

    @property
    def all_variables(self) -> Dict[str, Any]:  # pylint: disable=C0116
        return self.csvpath.csvpaths.results_manager.get_variables(self.paths_name)

    @property
    def paths_name(self) -> str:  # pylint: disable=C0116
        return self._paths_name

    @paths_name.setter
    def paths_name(self, paths_name: str) -> None:
        self._paths_name = paths_name  # pragma: no cover

    @property
    def file_name(self) -> str:  # pylint: disable=C0116
        return self._file_name

    @file_name.setter
    def file_name(self, file_name: str) -> None:
        self._file_name = file_name  # pragma: no cover

    # ==========================
    # lines collecting methods
    #

    @property
    def lines(self) -> List[List[Any]]:  # pylint: disable=C0116
        return self._lines

    @lines.setter
    def lines(self, ls: List[List[Any]]) -> None:
        self._lines = ls

    def append(self, line: List[Any]) -> None:
        if self._lines is None:
            self._lines = []
        self._lines.append(line)

    def __len__(self) -> int:
        if self._lines is None:
            self._lines = []  # pragma: no cover
        return len(self._lines)

    # ==========================

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

    @property
    def errors_count(self) -> int:  # pylint: disable=C0116
        return len(self._errors)

    def collect_error(self, error: Error) -> None:  # pylint: disable=C0116
        self._errors.append(error)

    @property
    def has_errors(self) -> bool:  # pylint: disable=C0116
        return self.errors_count > 0

    @property
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
        lastline = 0
        endline = -1
        try:
            # if we haven't started yet -- common situation -- we may blow up.
            lastline = self.csvpath.line_monitor.physical_line_number
            endline = self.csvpath.line_monitor.physical_end_line_number
        except Exception:
            pass
        return f"""Result
                   file:{self.csvpath.scanner.filename if self.csvpath.scanner else None};
                   name of paths:{self.paths_name};
                   name of file:{self.file_name};
                   valid:{self.csvpath.is_valid};
                   stopped:{self.csvpath.stopped};
                   last line processed:{lastline};
                   total file lines:{endline};
                   matches:{self.csvpath.match_count};
                   lines captured:{len(self.lines) if self.lines else 0};
                   print statements:{self.print_statements_count()};
                   errors:{len(self.errors)}"""
