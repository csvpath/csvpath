import csv
from typing import List, Dict, Any
from collections.abc import Iterator
from csvpath.matching.matcher import Matcher
from csvpath.scanning.scanner import Scanner

class NoFileException(Exception):
    pass

class CsvPath:

    def __init__(self, *, filename=None, delimiter=',', quotechar='"', block_print=True):
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
        self.variables:Dict[str,Any] = {}
        self.delimiter=delimiter
        self.quotechar=quotechar
        self.block_print = block_print
        self.total_lines = -1
        self._verbose = False

    def parse(self, data):
        self.scanner = Scanner()
        s, mat, mod = self._find_scan_match_modify(data)
        self.scan = s
        self.match = mat
        self.modify = mod
        self.scanner.parse(s)
        self._load_headers()
        self.get_total_lines()
        return self.scanner

    def verbose(self, set_verbose:bool=True) -> None:
        self._verbose = set_verbose

    # prints what the user needs to see
    def verbosity(self, msg:Any) -> None:
        if self._verbose:
            print(f"{msg}")

    # prints what the developer needs to see
    def print(self, msg:str) -> None:
        if not self.block_print:
            print(msg)

    def _load_headers(self) -> None:
        with open(self.scanner.filename, "r") as file:
            reader = csv.reader(file, delimiter=self.delimiter, quotechar=self.quotechar)
            for row in reader:
                self.headers = row
                break
        hs = self.headers[:]
        self.headers = []
        for header in hs:
            header = header.strip()
            header = header.replace(';','')
            header = header.replace(',','')
            header = header.replace('|','')
            header = header.replace('\t','')
            header = header.replace('`','')
            self.headers.append(header)
            self.verbosity(f"header: {header}")

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
                p = p+1
        scan = scan.strip()
        scan = scan if len(scan) > 0 else None
        matches = matches.strip()
        matches = matches if len(matches) > 0 else None
        modify = modify.strip()
        modify = modify if len(modify) > 0 else None
        self.verbosity(f"scan: {scan}")
        self.verbosity(f"matches: {matches}")
        self.verbosity(f"modify: {modify}")
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
        self.verbosity(f"filename: {self.scanner.filename}")
        total_lines = -1
        if self._verbose:
            total_lines = self.get_total_lines()
            self.verbosity(f"total lines: {total_lines}")

        with open(self.scanner.filename, "r") as file:
            reader = csv.reader(file, delimiter=self.delimiter, quotechar=self.quotechar)
            for line in reader:
                self.verbosity(f"line number: {self.line_number} of {total_lines}")
                if self.includes(self.line_number):
                    self.scan_count = self.scan_count + 1
                    self.print(f"CsvPath.next: line:{line}")
                    self.verbosity(f"scan count: {self.scan_count}")
                    if self.matches(line):
                        self.match_count = self.match_count + 1
                        self.verbosity(f"match count: {self.match_count}")
                        yield line
                self.line_number = self.line_number + 1

    def get_total_lines(self) -> int:
        if self.total_lines == -1:
            with open(self.scanner.filename, "r") as file:
                reader = csv.reader(file, delimiter=self.delimiter, quotechar=self.quotechar)
                for line in reader:
                    self.total_lines += 1
        return self.total_lines

    def current_line_number(self) -> int:
        return self.line_number

    def current_scan_count(self) -> int:
        return self.scan_count

    def current_match_count(self) -> int:
        return self.match_count

    def matches(self, line) -> bool:
        if not self.match:
            return True
        self.print(f"CsvPath.matches: the match path: {self.match}")

        matcher = Matcher(csvpath=self, data=self.match, line=line, headers=self.headers)
        matched = matcher.matches()
        return matched

    def set_variable(self, name:str, *, value:Any, tracking:Any=None) -> None:
        if not name:
            raise Exception("name cannot be None")
        self.print(f"CsvPath.set_variable: {name} = {value} for {tracking}")
        self.print(f"CsvPath.set_variable: current vars: {self.variables}")
        if name in self.variables:
            self.print(f"CsvPath.set_variable: existing value: {self.variables[name]}")
        else:
            self.print("CsvPath.set_variable: no existing value")
        if tracking:
            instances = self.variables[name]
            instances[tracking] = value
        else:
            self.variables[name] = value

    def get_variable(self, name:str,*,tracking:Any=None, set_if_none:Any=None) -> Any:
        if not name:
            raise Exception("name cannot be None")
        self.print(f"CsvPath.get_variable: name: {name}, tracking: {tracking}, set_if_none: {set_if_none}")
        self.print(f"CsvPath.get_variable: variables: {self.variables}")
        thevalue = None
        if tracking:
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
            if not thevalue and set_if_none:
                thedict[tracking] = set_if_none
                thevalue = set_if_none
            self.print(f"CsvPath.get_variable: name: {name}, tracking: {tracking}, thevalue: {thevalue}")
        else:
            if not name in self.variables:
                self.variables[name] = set_if_none
                thevalue = set_if_none
            thevalue = self.variables[name]
        self.print(f"CsvPath.get_variable: name: {name}, tracking: {tracking}, thevalue: {thevalue}")
        return thevalue


    def includes(self, line:int) -> bool:
        from_line = self.scanner.from_line
        to_line = self.scanner.to_line
        all_lines = self.scanner.all_lines
        these = self.scanner.these
        return self._includes(line, from_line=from_line, to_line=to_line, all_lines=all_lines, these=these)

    def _includes(self, line:int, *, from_line:int=None,
                  to_line:int=None, all_lines:bool=None, these:List[int]=[] ) -> bool:
        if line is None:
            return False
        if from_line is None and all_lines:
            return True
        if from_line is not None and all_lines:
            return line >= from_line
        if from_line == line:
            return True
        if from_line is not None and to_line is not None and from_line > to_line:
            return line >= to_line and line <= from_line
        if from_line is not None and to_line is not None:
            return line >= from_line and line <= to_line
        if line in these:
            return True
        if to_line is not None:
            return line < to_line
        return False

    def line_numbers(self) -> Iterator[int|str]:
        these = self.scanner.these
        from_line = self.scanner.from_line
        to_line = self.scanner.to_line
        all_lines = self.scanner.all_lines
        return self._line_numbers(these=these, from_line=from_line, to_line=to_line, all_lines=all_lines )

    def _line_numbers(self, *, these:List[int]=[],
                      from_line:int=None, to_line:int=None,
                      all_lines:bool=None) -> Iterator[int|str]:
        if len(these) > 0:
            for i in these:
                yield i
        else:
            if from_line is not None and to_line is not None and from_line > to_line:
                for i in range(to_line, from_line+1):
                    yield i
            elif from_line is not None and to_line is not None:
                for i in range(from_line, to_line+1):
                    yield i
            elif from_line is not None:
                if all_lines:
                    yield f"{from_line}..."
                else:
                    yield from_line
            elif to_line is not None:
                yield f"0..{to_line}"

    def collect_line_numbers(self) -> List[int|str]:
        these = self.scanner.these
        from_line = self.scanner.from_line
        to_line = self.scanner.to_line
        all_lines = self.scanner.all_lines
        return _collect_line_numbers(these=these, from_line=from_line, to_line=to_line, all_lines=all_lines)

    def _collect_line_numbers(self, *, these:List[int]=[],
                      from_line:int=None, to_line:int=None,
                      all_lines:bool=None )-> List[int|str]:
        collect = []
        for i in self._line_numbers(these=these, from_line=from_line, to_line=to_line, all_lines=all_lines):
            collect.append(i)
        return collect


