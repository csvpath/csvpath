import csv
from typing import List, Dict, Any
from collections.abc import Iterator
from csvpath.matching.matcher import Matcher
from csvpath.matching.expression_encoder import ExpressionEncoder
from csvpath.matching.expression_math import ExpressionMath
from csvpath.scanning.scanner import Scanner
import time


class NoFileException(Exception):
    pass


class CsvPath:
    def __init__(
        self,
        *,
        filename=None,
        delimiter=",",
        quotechar='"',
        block_print=True,
        skip_blank_lines=True,
    ):
        self.filename = filename
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
        self.block_print = block_print
        self.total_lines = -1
        self._dump_json = False
        self._do_math = False  # off by default, still experimental
        self._collect_matchers = False
        self.matchers = []
        self.jsons = []
        self.matcher = None
        self.skip_blank_lines = skip_blank_lines

    def dump_json(self):
        self._dump_json = not self._dump_json

    def parse(self, data):
        start = time.time()
        self.scanner = Scanner()
        s, mat, mod = self._find_scan_match_modify(data)
        self.scan = s
        self.match = mat
        self.modify = mod
        self.scanner.parse(s)
        end = time.time()
        print(f"parsed: {end - start}")
        self.get_total_lines_and_headers()
        return self.scanner

    # prints what the developer needs to see
    def print(self, msg: str) -> None:
        if not self.block_print:
            print(msg)

    def _find_scan_match_modify(self, data):
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
            path: {self.scanner.path}
            filename: {self.filename}
            parser: {self.scanner}
            from_line: {self.scanner.from_line}
            to_line: {self.scanner.to_line}
            all_lines: {self.scanner.all_lines}
            these: {self.scanner.these}
        """

    @property
    def from_line(self):
        return self.scanner.from_line

    @property
    def to_line(self):
        return self.scanner.to_line

    @property
    def all_lines(self):
        return self.scanner.all_lines

    @property
    def path(self):
        return self.scanner.path

    @property
    def these(self):
        return self.scanner.these

    @property
    def filename(self):
        return self.file_name

    @filename.setter
    def filename(self, f):
        self.file_name = f

    def collect(self) -> List[List[Any]]:
        lines = []
        for _ in self.next():
            _ = _[:]
            lines.append(_)
        return lines

    def next(self):
        if self.scanner.filename is None:
            raise NoFileException("there is no filename")
        with open(self.scanner.filename, "r") as file:
            reader = csv.reader(
                file, delimiter=self.delimiter, quotechar=self.quotechar
            )
            start = time.time()
            for line in reader:
                if self.skip_blank_lines and len(line) == 0:
                    continue
                if self.scanner.includes(self.line_number):
                    self.scan_count = self.scan_count + 1
                    # from datetime import timedelta
                    # startmatch = time.perf_counter()
                    b = self.matches(line)
                    # endmatch = time.time()
                    # duration = timedelta(seconds=time.perf_counter()-startmatch)
                    if b:
                        self.match_count = self.match_count + 1
                        yield line
                    # if self.scan_count < 100:
                    #    print(f"match {self.scan_count}: {duration}")
                self.line_number = self.line_number + 1
            end = time.time()
            print(f"iterated: {end - start}")

    def get_total_lines(self) -> int:
        if self.total_lines == -1:
            return self.get_total_lines_and_headers()
        return self.total_lines

    def get_total_lines_and_headers(self) -> int:
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
            print(f"lines and headers: {end - start}")
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

    def do_math(self):
        self._do_math = not self._do_math

    def collect_matchers(self):
        self._collect_matchers = not self._collect_matchers

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
        matcher = self.matcher

        if self._do_math:
            em = ExpressionMath()
            for e in matcher.expressions:
                em.do_math(e[0])

        if self._dump_json:
            jsonstr = ExpressionEncoder().valued_list_to_json(matcher.expressions)
            self.jsons.append(jsonstr)

        matched = matcher.matches()
        if self._collect_matchers:  # and matched
            self.matchers.append(matcher)

        return matched

    def set_variable(self, name: str, *, value: Any, tracking: Any = None) -> None:
        if not name:
            raise Exception("name cannot be None")
        if name in self.variables:
            self.print(f"CsvPath.set_variable: existing value: {self.variables[name]}")
        else:
            self.print("CsvPath.set_variable: no existing value")
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
            raise Exception("name cannot be None")
        thevalue = None
        if tracking is not None:
            thedict = None
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
            thevalue = thedict.get(tracking)
            if not thevalue and set_if_none is not None:
                thedict[tracking] = set_if_none
                thevalue = set_if_none
        else:
            if name not in self.variables:
                self.variables[name] = set_if_none
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
