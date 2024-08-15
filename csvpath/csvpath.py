import csv
import time
from typing import List, Dict, Any
from collections.abc import Iterator
from . import Matcher
from . import Scanner
from . import ExpressionEncoder
from . import (
    VariableException,
    InputException,
    FileException,
    ParsingException,
    FormatException,
    ProcessingException,
    ConfigurationException,
)


class CsvPath:
    def __init__(
        self,
        *,
        csvpaths=None,
        delimiter=",",
        quotechar='"',
        skip_blank_lines=True,
    ):
        self.csvpaths = csvpaths
        self.scanner = None
        self.value = None
        self.scan = None
        self.match = None
        self.modify = None
        self.headers = None
        self.line_number = 0
        self.scan_count = 0
        self.match_count = 0
        self.variables: Dict[str, Any] = {}
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.total_lines = -1
        self.matchers = []
        self.jsons = []
        self.matcher = None
        self.skip_blank_lines = skip_blank_lines
        self.stopped = False
        self.last_row_time = -1
        self.rows_time = -1
        self.total_iteration_time = -1
        self._advance = 0
        self._is_valid = True

    def parse(self, data):
        # start = time.time()
        self.scanner = Scanner(csvpath=self)
        data = self._update_file_path(data)
        s, mat, mod = self._find_scan_match_modify(data)
        self.scan = s
        self.match = mat
        self.modify = mod
        self.scanner.parse(s)
        # end = time.time()
        # end - start
        if self.scanner.filename:
            self.get_total_lines_and_headers()
        return self.scanner

    def parse_named_path(self, name):
        if not self.csvpaths:
            raise ConfigurationException("No CsvPaths object available")
        np = self.csvpaths.get_named_path(name)
        if not np:
            raise ConfigurationException(f"Named path {name} not found")
        self.parse(np)

    def _update_file_path(self, data: str):
        if data is None:
            raise InputException("The csvpath string cannot be None")
        if self.csvpaths is None:
            return data
        name = self._get_name(data)
        path = self.csvpaths.files_manager.get_named_file(name)
        if path is None:
            return data
        elif path == name:
            return data
        else:
            return data.replace(name, path)

    def _get_name(self, data: str):
        if self.csvpaths is None:
            return data
        else:
            data = data.strip()
            if data[0] == "$":
                name = data[1 : data.find("[")]
                return name
            else:
                raise FormatException(f"Must start with '$', not {data[0]}")
            return data

    def _find_scan_match_modify(self, data):
        if data is None or not isinstance(data, str):
            raise InputException("Not a csvpath string")
        scan = ""
        matches = ""
        modify = ""
        p = 0
        for i, c in enumerate(data):
            if p == 0:
                scan = scan + c
            elif p == 1:
                matches = matches + c
            else:
                modify = modify + c
            if c == "]":
                p = p + 1
        scan = scan.strip()
        scan = scan if len(scan) > 0 else None
        matches = matches.strip()
        matches = matches if len(matches) > 0 else None
        modify = modify.strip()
        modify = modify if len(modify) > 0 else None
        return scan, matches, modify

    def __str__(self):
        return f"""
            path: {self.scanner.path if self.scanner else None}
            parser: {self.scanner}
            from_line: {self.scanner.from_line if self.scanner else None}
            to_line: {self.scanner.to_line if self.scanner else None}
            all_lines: {self.scanner.all_lines if self.scanner else None}
            these: {self.scanner.these if self.scanner else None}
        """

    @property
    def is_valid(self) -> bool:  # pragma: no cover
        return self._is_valid

    @is_valid.setter
    def is_valid(self, tf: bool) -> None:
        self._is_valid = tf

    @property
    def from_line(self):  # pragma: no cover
        if self.scanner is None:
            raise ParsingException("No scanner available. Have you parsed a csvpath?")
        return self.scanner.from_line

    @property
    def to_line(self):  # pragma: no cover
        if self.scanner is None:
            raise ParsingException("No scanner available. Have you parsed a csvpath?")
        return self.scanner.to_line

    @property
    def all_lines(self):  # pragma: no cover
        if self.scanner is None:
            raise ParsingException("No scanner available. Have you parsed a csvpath?")
        return self.scanner.all_lines

    @property
    def path(self):  # pragma: no cover
        if self.scanner is None:
            raise ParsingException("No scanner available. Have you parsed a csvpath?")
        return self.scanner.path

    @property
    def these(self):  # pragma: no cover
        if self.scanner is None:
            raise ParsingException("No scanner available. Have you parsed a csvpath?")
        return self.scanner.these

    def stop(self) -> None:
        self.stopped = True

    def collect(self, nexts: int = -1) -> List[List[Any]]:
        if nexts < -1:
            raise ProcessingException(
                "Input must be >= -1. -1 means collect to the end of the file."
            )
        lines = []
        for _ in self.next():
            _ = _[:]
            lines.append(_)
            if nexts == -1:
                continue
            elif nexts > 1:
                nexts -= 1
            else:
                break
        return lines

    def advance(self, ff: int = -1) -> None:
        """Advances the iteration by ff rows. The rows will be seen and
        variables and side effects will happen.
        """
        if ff == -1:
            self._advance = self.total_lines - self.line_number - self._advance
        else:
            self._advance += ff
        if self._advance > self.total_lines:
            self._advance = self.total_lines

    def fast_forward(self) -> None:
        """Runs the path for all rows of the file. Variables are collected
        and side effects like print happen. No lines are collected.
        """
        for _ in self.next():
            pass

    def next(self):
        if self.scanner.filename is None:
            raise FileException("There is no filename")
        with open(self.scanner.filename, "r") as file:
            reader = csv.reader(
                file, delimiter=self.delimiter, quotechar=self.quotechar
            )
            start = time.time()
            for line in reader:
                if self.skip_blank_lines and len(line) == 0:
                    pass
                elif self.scanner.includes(self.line_number):
                    self.scan_count = self.scan_count + 1
                    startmatch = time.perf_counter_ns()
                    b = self.matches(line)
                    endmatch = time.perf_counter_ns()
                    if b:
                        self.match_count = self.match_count + 1
                        if self._advance != 0:
                            self._advance -= 1
                        else:
                            yield line
                    t = (endmatch - startmatch) / 1000000
                    self.last_row_time = t
                    self.rows_time += t
                self.line_number = self.line_number + 1
                if self.stopped:
                    break
            end = time.time()
            self.total_iteration_time = end - start

    def get_total_lines(self) -> int:
        if self.total_lines == -1:
            return self.get_total_lines_and_headers()
        return self.total_lines

    def get_total_lines_and_headers(self) -> int:
        # do we need a way to disable the line count to speed up big files?
        if self.total_lines == -1:
            start = time.time()
            with open(self.scanner.filename, "r") as file:
                reader = csv.reader(
                    file, delimiter=self.delimiter, quotechar=self.quotechar
                )
                i = 0
                for line in reader:
                    if i == 0:
                        self.headers = line
                        i += 1
                    self.total_lines += 1
            hs = self.headers[:]
            self.headers = []
            for header in hs:
                header = header.strip()
                header = header.replace(";", "")
                header = header.replace(",", "")
                header = header.replace("|", "")
                header = header.replace("\t", "")
                header = header.replace("`", "")
                self.headers.append(header)
            end = time.time()
            end - start
        return self.total_lines

    def _load_headers(self) -> None:
        with open(self.scanner.filename, "r") as file:
            reader = csv.reader(
                file, delimiter=self.delimiter, quotechar=self.quotechar
            )
            for row in reader:
                self.headers = row
                break
        hs = self.headers[:]
        self.headers = []
        for header in hs:
            header = header.strip()
            header = header.replace(";", "")
            header = header.replace(",", "")
            header = header.replace("|", "")
            header = header.replace("\t", "")
            header = header.replace("`", "")
            self.headers.append(header)

    def current_line_number(self) -> int:
        return self.line_number

    def current_scan_count(self) -> int:
        return self.scan_count

    def current_match_count(self) -> int:
        return self.match_count

    def matches(self, line) -> bool:
        if not self.match:
            return True
        if self.matcher is None:
            self.matcher = Matcher(
                csvpath=self, data=self.match, line=line, headers=self.headers
            )
        else:
            self.matcher.reset()
            self.matcher.line = line
        matched = self.matcher.matches()
        return matched

    def set_variable(self, name: str, *, value: Any, tracking: Any = None) -> None:
        if not name:
            raise VariableException("Name cannot be None")
        if tracking is not None:
            if name not in self.variables:
                self.variables[name] = {}
            instances = self.variables[name]
            instances[tracking] = value
        else:
            self.variables[name] = value

    def get_variable(
        self, name: str, *, tracking: Any = None, set_if_none: Any = None
    ) -> Any:
        if not name:
            raise VariableException("Name cannot be None")
        thevalue = None
        if tracking is not None:
            thedict = None
            thevalue = None
            if name in self.variables:
                thedict = self.variables[name]
                if not thedict:
                    thedict = {}
                    self.variables[name] = thedict
                    thedict[tracking] = set_if_none
            else:
                thedict = {}
                thedict[tracking] = set_if_none
                self.variables[name] = thedict
            if isinstance(thedict, dict):
                thevalue = thedict.get(tracking)
            if not thevalue and set_if_none is not None:
                thedict[tracking] = set_if_none
                thevalue = set_if_none
        else:
            if name not in self.variables:
                if set_if_none is not None:
                    self.variables[name] = set_if_none
                    thevalue = set_if_none
            else:
                thevalue = self.variables[name]
        return thevalue

    def line_numbers(self) -> Iterator[int | str]:
        these = self.scanner.these
        from_line = self.scanner.from_line
        to_line = self.scanner.to_line
        all_lines = self.scanner.all_lines
        return self._line_numbers(
            these=these, from_line=from_line, to_line=to_line, all_lines=all_lines
        )

    def _line_numbers(
        self,
        *,
        these: List[int] = [],
        from_line: int = None,
        to_line: int = None,
        all_lines: bool = None,
    ) -> Iterator[int | str]:
        if len(these) > 0:
            for i in these:
                yield i
        else:
            if from_line is not None and to_line is not None and from_line > to_line:
                for i in range(to_line, from_line + 1):
                    yield i
            elif from_line is not None and to_line is not None:
                for i in range(from_line, to_line + 1):
                    yield i
            elif from_line is not None:
                if all_lines:
                    yield f"{from_line}..."
                else:
                    yield from_line
            elif to_line is not None:
                yield f"0..{to_line}"

    def collect_line_numbers(self) -> List[int | str]:
        if self.scanner is None:
            raise ParsingException("No scanner available. Have you parsed a csvpath?")
        these = self.scanner.these
        from_line = self.scanner.from_line
        to_line = self.scanner.to_line
        all_lines = self.scanner.all_lines
        return self._collect_line_numbers(
            these=these, from_line=from_line, to_line=to_line, all_lines=all_lines
        )

    def _collect_line_numbers(
        self,
        *,
        these: List[int] = [],
        from_line: int = None,
        to_line: int = None,
        all_lines: bool = None,
    ) -> List[int | str]:
        collect = []
        for i in self._line_numbers(
            these=these, from_line=from_line, to_line=to_line, all_lines=all_lines
        ):
            collect.append(i)
        return collect

    def header_index(self, name: str) -> int:
        if not self.headers:
            return None
        i = -1
        for i, n in enumerate(self.headers):
            if n == name:
                return i
        return i
