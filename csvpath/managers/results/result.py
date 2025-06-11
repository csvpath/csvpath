# pylint: disable=C0114
import os
from uuid import UUID
import uuid
import json
from datetime import datetime
from typing import Any
from csvpath import CsvPath
from csvpath.managers.errors.error import Error
from csvpath.managers.errors.error_collector import ErrorCollector
from csvpath.managers.listener import Listener
from csvpath.managers.metadata import Metadata
from csvpath.util.printer import Printer
from csvpath.util.exceptions import CsvPathsException
from csvpath.util.line_spooler import LineSpooler, CsvLineSpooler
from .result_serializer import ResultSerializer
from .readers.readers import ResultReadersFacade
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.util.file_readers import DataFileReader


class Result(ErrorCollector, Printer, Listener):  # pylint: disable=R0902
    """This class handles the results for a single CsvPath in the
    context of a CsvPaths run that may apply any number of CsvPath
    instances against the same file.
    """

    def __init__(
        self,
        *,
        paths_name: str,
        run_dir: str = None,
        lines: list[list[Any]] = None,
        csvpath: CsvPath = None,
        file_name: str = None,
        run_index: int = None,
        run_time: datetime = None,
        runtime_data: dict = None,
        by_line: bool = False,
        run_uuid: UUID,
    ):
        """@private"""
        ErrorCollector.__init__(self)
        Printer.__init__(self)
        Listener.__init__(self, csvpath.config if csvpath is not None else None)
        self._csvpath = None
        self._uuid = None
        self._runtime_data = runtime_data
        self._paths_name = paths_name
        self._file_name = file_name
        self._preceding = None
        self._print_count = 0
        self._last_line = None
        self.run_index = f"{run_index}"
        self._run_time = run_time
        self._run_dir = run_dir
        #
        # actual_data_file is the file the scanner found that we actually iterated through.
        # if we are source-mode preceding this may not be the named-file path, which is the
        # origin data file.
        #
        self._actual_data_file = None
        self._origin_data_file = None
        self._by_line = by_line
        #
        # data_file_path is the path to data.csv of this result
        #
        self._data_file_path = None
        #
        # are set here:
        #   - error listener / error_collector
        #   - printer
        #
        self.csvpath = csvpath
        #
        #
        #
        if (
            csvpath
            and csvpath.metadata is None
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
        #
        # readers
        # add these last so that we can be sure they have access to everything they need.
        # primarily, run_dir, instance, and csvpath
        #
        self._errors: list[Error] = None
        self._printouts: dict[str, list[str]] = None
        self._unmatched: list[list[Any]] = None
        self._lines: list[list[Any]] = None
        self._readers_facade = ResultReadersFacade(self)
        self._run_uuid = run_uuid

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

    @property
    def run_uuid(self) -> UUID:
        if self._run_uuid is None:
            self._run_uuid = uuid.uuid4()
        return self._run_uuid

    @uuid.setter
    def uuid(self, u: UUID) -> None:
        if not isinstance(u, UUID):
            raise ValueError("Uuid must be a UUID")
        self._uuid = u

    @run_uuid.setter
    def run_uuid(self, u: UUID) -> None:
        if not isinstance(u, UUID):
            raise ValueError("Uuid must be a UUID")
        self._run_uuid = u

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
    def run_manifest(self) -> dict:
        p = self.run_dir
        p = os.path.join(p, "manifest.json")
        with DataFileReader(p) as reader:
            return json.load(reader.source)

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
    def manifest(self) -> dict:
        p = self.instance_dir
        p = os.path.join(p, "manifest.json")
        with DataFileReader(p) as reader:
            return json.load(reader.source)

    @property
    def identity_or_index(self) -> str:
        s = self._csvpath.identity
        if f"{s}".strip() == "":
            s = self.run_index
        return s

    @property
    def index(self) -> int:
        ri = self.run_index
        if ri is None:
            return None
        ri = ri.strip()
        ri = ExpressionUtility.to_int(ri)
        return ri

    @property
    def paths_name(self) -> str:  # pylint: disable=C0116
        return self._paths_name

    @paths_name.setter
    def paths_name(self, paths_name: str) -> None:
        self._paths_name = paths_name  # pragma: no cover

    #
    # this is the named-file name, not a physical file name
    #
    @property
    def file_name(self) -> str:  # pylint: disable=C0116
        return self._file_name

    @file_name.setter
    def file_name(self, file_name: str) -> None:
        self._file_name = file_name  # pragma: no cover

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
    def last_line(self):  # pylint: disable=C0116
        """@private"""
        return self._last_line

    #
    # =============== LISTENING ===============
    #
    def metadata_update(self, mdata: Metadata) -> None:
        """@private"""
        if isinstance(mdata, Error):
            self.collect_error(mdata)

    #
    # =============== CSVPATH =================
    #

    @property
    def csvpath(self) -> CsvPath:  # pylint: disable=C0116
        return self._csvpath

    @csvpath.setter
    def csvpath(self, path: CsvPath) -> None:
        """@private"""
        # during testing or for some other reason we may receive None
        # let's assume the dev knows what they're doing and just go with it.
        if path is not None:
            path.error_manager.add_internal_listener(self)
            path.add_printer(self)
        self._csvpath = path

    #
    # =============== METADATA =================
    #

    @property
    def metadata(self) -> dict[str, Any]:  # pylint: disable=C0116
        return self.csvpath.metadata  # pragma: no cover

    #
    # =============== VARIABLES =================
    #

    @property
    def variables(self) -> dict[str, Any]:  # pylint: disable=C0116
        return self.csvpath.variables  # pragma: no cover

    @property
    def all_variables(self) -> dict[str, Any]:  # pylint: disable=C0116
        return self.csvpath.csvpaths.results_manager.get_variables(self.paths_name)

    #
    # =============== ERRORS =================
    #

    @property
    def errors(self) -> list[Error]:  # pylint: disable=C0116
        #
        # if none, use reader
        #
        if self._errors is None:
            self._errors = self._readers_facade.errors
        return self._errors

    @errors.setter
    def errors(self, errors: list[Error]) -> None:
        self._errors = errors

    @property
    def errors_count(self) -> int:  # pylint: disable=C0116
        if self.errors:
            return len(self.errors)
        return 0

    def collect_error(self, error: Error) -> None:  # pylint: disable=C0116
        """@private"""
        if self.errors is not None:
            self.errors.append(error)

    def has_errors(self) -> bool:
        return self.errors_count > 0

    #
    # =============== PRINTOUTS =================
    #

    @property
    def printouts(self) -> dict[str, list[str]]:
        #
        # if none, use reader
        #
        if self._printouts is None:
            self._printouts = self._readers_facade.printouts
        return self._printouts

    def get_printouts(self, name="default") -> dict[str, list[str]]:
        if self.printouts and name in self.printouts:
            return self.printouts[name]
        return []

    def set_printouts(self, name: str, lines: list[str]) -> None:
        """@private"""
        self.printouts[name] = lines

    def has_printouts(self) -> bool:  # pylint: disable=C0116
        if len(self.printouts) > 0:
            for k, v in self.printouts.items():
                if len(v) > 0:
                    return True
        return False

    @property
    def lines_printed(self) -> int:  # pylint: disable=C0116
        """@private"""
        return self._print_count

    def print(self, string: str) -> None:  # pylint: disable=C0116
        """@private"""
        self.print_to("default", string)

    def print_to(self, name: str, string: str) -> None:  # pylint: disable=C0116
        """@private"""
        self._print_count += 1
        if name not in self.printouts:
            self.printouts[name] = []
        self.printouts[name].append(string)
        self._last_line = string

    def dump_printing(self) -> None:  # pylint: disable=C0116
        """@private"""
        for k, v in self.printouts.items():
            for line in v:
                print(f"{k}: {line}")
            print("")

    def print_statements_count(self) -> int:  # pylint: disable=C0116
        """@private"""
        i = 0
        for name in self.printouts:
            i += len(self.printouts[name]) if self.printouts[name] else 0
        return i

    #
    # =============== LINES =================
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
            self._lines = self._readers_facade.lines
        return self._lines

    @lines.setter
    def lines(self, ls: list[list[Any]] | LineSpooler) -> None:
        """@private"""
        if self._lines and isinstance(self._lines, LineSpooler):
            self._lines.close()
        self._lines = ls

    def append(self, line: list[Any]) -> None:
        """@private"""
        self.lines.append(line)

    def __len__(self) -> int:
        if self.lines is not None:
            if isinstance(self.lines, list):
                return len(self.lines)
            i = 0
            #
            # is a LineSpooler
            #
            for _ in self.lines.next():
                i += 1
            return i
        return None

    #
    # =============== UNMATCHED =================
    #

    @property
    def unmatched(self) -> list[list[Any]]:
        if self._unmatched is None:
            #
            # we can assume the caller wants a container for lines. in that case,
            # we want them to have a container that serializes lines as they come in
            # rather than waiting for them all to arrive before writing to disk.
            #
            # for today we'll just default to CsvLineSpooler, but assume we'll work
            # in other options later.
            #
            self._unmatched = self._readers_facade.unmatched
        return self._unmatched

    @unmatched.setter
    def unmatched(self, lines: list[list[Any]]) -> None:
        """@private"""
        self._unmatched = lines

    #
    # ===========================================
    #

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
                   index: {self.index};
                   identity: {self.identity_or_index};
                   valid:{self.csvpath.is_valid};
                   stopped:{self.csvpath.stopped};
                   last line processed:{lastline};
                   total file lines:{endline};
                   matches:{self.csvpath.match_count};
                   lines matched:{len(self._lines) if self._lines and not isinstance(self._lines, LineSpooler) else -1};
                   lines unmatched:{len(self.unmatched) if self.unmatched else 0};
                   print statements:{self.print_statements_count()};
                   errors:{len(self.errors) if self.errors else -1}"""
