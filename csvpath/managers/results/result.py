# pylint: disable=C0114
import os
from uuid import UUID
import uuid
from datetime import datetime
from typing import Any
from csvpath.util.error import Error, ErrorCollector
from csvpath.util.printer import Printer
from csvpath.util.exceptions import CsvPathsException
from csvpath import CsvPath
from csvpath.util.line_spooler import LineSpooler, CsvLineSpooler
from .result_serializer import ResultSerializer


class Result(ErrorCollector, Printer):  # pylint: disable=R0902
    """This class handles the results for a single CsvPath in the
    context of a CsvPaths run that may apply any number of CsvPath
    instances against the same file.
    """

    # re: R0902: disagree that there's too many attributes in this case

    def __init__(
        self,
        *,
        lines: list[list[Any]] = None,
        csvpath: CsvPath,
        file_name: str,
        paths_name: str,
        run_index: int,
        run_time: datetime,
        run_dir: str,
        runtime_data: dict = None,
        by_line: bool = False,
    ):
        self._lines: list[list[Any]] = None
        self._csvpath = None
        self._runtime_data = runtime_data
        self._paths_name = paths_name
        self._file_name = file_name
        self._preceding = None
        self._errors = []
        self._printouts = {}
        self._print_count = 0
        self._last_line = None
        # use the properties so error_collector, etc. is set correctly
        self.csvpath = csvpath
        # self.lines = lines
        self.run_index = f"{run_index}"
        self._run_time = run_time
        self._run_dir = run_dir
        self._unmatched = None
        self._uuid = None
        #
        # data_file_path is the path to data.csv of this result
        #
        self._data_file_path = None
        #
        # actual_data_file is the file the scanner found that we actually iterated through.
        # if we are source-mode preceding this may not be the named-file path, which is the
        # origin data file.
        #
        self._actual_data_file = None
        self._origin_data_file = None
        self._by_line = by_line
        if (
            csvpath.metadata is None
            or csvpath.identity is None
            or csvpath.identity == ""
        ):
            if csvpath.metadata is None:
                raise CsvPathsException(
                    "Metadata cannot be None. Check order of operations."
                )
            #
            # "NAME" is the least favored identifier. if we parse metadata after setting this
            # identity and the csvpath uses any of the other five identifiers it will take
            # precedence over this index. if the csvpath uses NAME it will overwrite.
            #
            csvpath.metadata["NAME"] = self.run_index

    @property
    def actual_data_file(self) -> str:
        if self._actual_data_file is None:
            if self.csvpath.scanner:
                self._actual_data_file = self.csvpath.scanner.filename
        return self._actual_data_file

    @property
    def origin_data_file(self) -> str:
        if self._origin_data_file is None:
            self._origin_data_file = self.csvpath.csvpaths.file_manager.get_named_file(
                self.file_name
            )
        return self._origin_data_file

    @property
    def uuid(self) -> UUID:
        if self._uuid is None:
            self._uuid = uuid.uuid4()
        return self._uuid

    @uuid.setter
    def uuid(self, u: UUID) -> None:
        if not isinstance(u, UUID):
            raise ValueError("Uuid must be a UUID")
        self._uuid = u

    @property
    def run_time(self) -> datetime:
        return self._run_time

    @property
    def run_dir(self) -> str:
        return self._run_dir

    @run_dir.setter
    def run_dir(self, d: str) -> None:
        self._run_dir = d

    @property
    def by_line(self) -> bool:
        return self._by_line

    @property
    def source_mode_preceding(self) -> bool:
        if self._preceding is None:
            self._preceding = self.csvpath.data_from_preceding
        return self._preceding

    @property
    def data_file_path(self) -> str:
        return os.path.join(self.instance_dir, "data.csv")

    @property
    def instance_dir(self) -> str:
        #
        # would we ever need self.csvpath before it is set? seems unlikely.
        #
        i_dir = ResultSerializer(self.csvpath.config.archive_path).get_instance_dir(
            run_dir=self.run_dir, identity=self.identity_or_index
        )
        return i_dir

    @property
    def identity_or_index(self) -> str:
        s = self._csvpath.identity
        if f"{s}".strip() == "":
            s = self.run_index
        return s

    @property
    def metadata(self) -> dict[str, Any]:  # pylint: disable=C0116
        return self.csvpath.metadata  # pragma: no cover

    @property
    def variables(self) -> dict[str, Any]:  # pylint: disable=C0116
        return self.csvpath.variables  # pragma: no cover

    @property
    def all_variables(self) -> dict[str, Any]:  # pylint: disable=C0116
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
    def lines(self) -> list[list[Any]]:
        if self._lines is None:
            #
            # we can assume the caller wants a container for lines. in that case,
            # we want them to have a container that serializes lines as they come in
            # rather than waiting for them all to arrive before writing to disk.
            #
            # for today we'll just default to CsvLineSpooler, but assume we'll work
            # in other options later.
            #
            self._lines = CsvLineSpooler(self)
        return self._lines

    @lines.setter
    def lines(self, ls: list[list[Any]]) -> None:
        if self._lines and isinstance(self._lines, LineSpooler):
            self._lines.close()
        self._lines = ls

    def append(self, line: list[Any]) -> None:
        self.lines.append(line)

    def __len__(self) -> int:
        if isinstance(self.lines, list):
            return len(self._lines)
        i = 0
        for _ in self.lines.next():
            i += 1
        return i

    @property
    def unmatched(self) -> list[list[Any]]:
        return self._unmatched

    @unmatched.setter
    def unmatched(self, lines: list[list[Any]]) -> None:
        self._unmatched = lines

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
    def errors(self) -> list[Error]:  # pylint: disable=C0116
        return self._errors

    @errors.setter
    def errors(self, errors: list[Error]) -> None:
        self._errors = errors

    @property
    def errors_count(self) -> int:  # pylint: disable=C0116
        return len(self._errors)

    def collect_error(self, error: Error) -> None:  # pylint: disable=C0116
        self._errors.append(error)

    def has_errors(self) -> bool:
        return self.errors_count > 0

    @property
    def is_valid(self) -> bool:  # pylint: disable=C0116
        # if the csvpath has not been run -- e.g. because it represents results that were
        # saved to disk and reloaded -- it won't have a run started time.
        if self._csvpath and self._csvpath.run_started_at is not None:
            return self._csvpath.is_valid
        elif self._runtime_data and "valid" in self._runtime_data:
            return self._runtime_data["valid"]
        return False

    @property
    def printouts(self) -> list[str]:
        """this method returns the default printouts. use get_printout_by_name
        for specific printouts"""
        if self._printouts is None:
            self._printouts = []
        return self._printouts["default"] if "default" in self._printouts else []

    def get_printouts(self) -> dict[str, list[str]]:
        return self._printouts

    def set_printouts(self, name: str, lines: list[str]) -> None:
        if self._printouts is None:
            self._printouts = {}
        self._printouts[name] = lines

    def get_printout_by_name(self, name: str) -> list[str]:  # pylint: disable=C0116
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
        endline = endline + 1
        return f"""Result
                   file:{self.csvpath.scanner.filename if self.csvpath.scanner else None};
                   name of paths:{self.paths_name};
                   name of file:{self.file_name};
                   run results dir:{self.run_dir};
                   valid:{self.csvpath.is_valid};
                   stopped:{self.csvpath.stopped};
                   last line processed:{lastline};
                   total file lines:{endline};
                   matches:{self.csvpath.match_count};
                   lines matched:{len(self._lines) if self._lines and not isinstance(self._lines, LineSpooler) else -1};
                   lines unmatched:{len(self.unmatched) if self.unmatched else 0};
                   print statements:{self.print_statements_count()};
                   errors:{len(self.errors)}"""
