import __main__
import os
from typing import Any, List
import dateutil.parser
from datetime import datetime, timezone
from ..metadata import Metadata
from csvpath.matching.productions.matchable import Matchable


class Error(Metadata):
    """error metadata data"""

    def __init__(self, *, source=None, msg=None, error_manager=None):
        config = None
        #
        # should this also check for csvpaths? our error_mgr can
        # exist w/o a csvpath when csvpaths is doing file loads.
        #
        csvpath = None
        if error_manager:
            if error_manager.csvpath is None and error_manager.csvpaths is None:
                raise ValueError("ErrorManager must hold a CsvPath and/or a CsvPaths")
            config = (
                error_manager.csvpath.config
                if error_manager.csvpath
                else error_manager.csvpaths.config
            )
            csvpath = error_manager.csvpath
            self.named_file_name = csvpath.named_file_name if csvpath else None
            self.named_paths_name = csvpath.named_paths_name if csvpath else None
            self.identity: str = csvpath.identity if error_manager.csvpath else None
        super().__init__(config)
        self.expression_index: int = -1
        self.source: str = None
        if source and isinstance(source, Matchable):
            self.expression_index = source.my_expression.index
            self.source = source.my_chain
        else:
            self.source = f"{source}"
        self.line_count: int = -1
        self.match_count: int = -1
        self.scan_count: int = -1
        self.message: str = msg
        self.expanded_message: str = None
        self.filename: str = None
        self.run_dir = None
        if error_manager and error_manager.csvpaths:
            self.run_dir = error_manager.csvpaths.last_run_dir
        self.cwd = os.getcwd()
        self.pid = os.getpid()

        self.load(csvpath)

    def load(self, csvpath) -> None:
        if csvpath is None:
            return
        self.filename = csvpath.scanner.filename if csvpath.scanner else None
        self.line_count: csvpath.line_monitor.physical_line_number
        self.match_count: csvpath.current_match_count
        self.scan_count: csvpath.current_scan_count

    def __eq__(self, e) -> bool:
        return (
            self.line_count == e.line_count
            and self.match_count == e.match_count
            and self.scan_count == e.scan_count
            and self.named_paths_name == e.named_paths_name
            and self.named_file_name == e.named_file_name
            and self.source == e.source
            and self.message == e.message
            and self.identity == e.identity
            and self.filename == e.filename
            and self.run_dir == e.run_dir
            and f"{self.time}" == f"{e.time}"
        )

    def how_eq(self, e) -> bool:
        print(f"Error.how_eq: is equal? {self.__eq__(e)}:")
        b = self.line_count == e.line_count
        print(f"line_count:    {b}: {self.line_count} == {e.line_count}")
        b = self.match_count == e.match_count
        print(f"match_count:   {b}: {self.match_count} == {e.match_count}")
        b = self.scan_count == e.scan_count
        print(f"scan_count:    {b}: {self.scan_count} == {e.scan_count}")
        b = self.time == e.time
        print(f"time:            {b}: {self.time} == {e.time}")
        b = self.named_paths_name == e.named_paths_name
        print(f"named_paths_name: {b}: {self.named_paths_name} == {e.named_paths_name}")
        b = self.named_file_name == e.named_file_name
        print(f"named_file_name: {b}: {self.named_file_name} == {e.named_file_name}")
        b = self.identity == e.identity
        print(f"identity: {b}: {self.identity} == {e.identity}")
        b = f"{self.source}".strip() == f"{e.source}".strip()
        print(f"source:        {b}: {self.source} == {e.source}")
        b = self.message == e.message
        print(f"message:       {b}: {self.message} == {e.message}")
        b = self.filename == e.filename
        print(f"filename:      {b}: {self.filename} == {e.filename}")

    def to_json(self) -> dict:
        ret = {
            "line_count": self.line_count,
            "match_count": self.match_count,
            "scan_count": self.scan_count,
            "source": self.source,
            "message": self.message,
            "named_paths_name": self.named_paths_name,
            "named_file_name": self.named_file_name,
            "identity": self.identity,
            "filename": self.filename,
            "time": f"{self.time}",
        }
        if self.run_dir is not None:
            ret["run_dir"] = self.run_dir
        return ret

    def from_json(self, j: dict) -> None:
        if "line_count" in j:
            self.line_count = j["line_count"]
        if "match_count" in j:
            self.match_count = j["match_count"]
        if "scan_count" in j:
            self.scan_count = j["scan_count"]
        if "source" in j:
            self.source = j["source"]
        if "message" in j:
            self.message = j["message"]
        if "named_paths_name" in j:
            self.named_paths_name = j["named_paths_name"]
        if "named_file_name" in j:
            self.named_file_name = j["named_file_name"]
        if "identity" in j:
            self.identity = j["identity"]
        if "filename" in j:
            self.filename = j["filename"]
        if "run_dir" in j:
            self.run_dir = j["run_dir"]
        if "time" in j:
            time = dateutil.parser.parse(j["time"])
            self.time = time

    def __str__(self) -> str:
        #
        #
        #
        #
        #
        #
        string = f"""Error
time: {self.time_string},
uuid: {self.uuid_string},
cwd: {self.cwd},
pid: {self.pid},
archive: {self.archive_name},
archive path: {self.archive_path},
named_files_root: {self.named_files_root},
named_paths_root: {self.named_paths_root},
hostname: {self.hostname},
ip_address: {self.ip_address},
username: {self.username},
named_paths_name: {self.named_paths_name if self.named_paths_name else ""},
named_file_name: {self.named_file_name if self.named_file_name else ""},
run_dir: {self.run_dir if self.run_dir else ""},
filename: {self.filename if self.filename else ""},
path identity: {self.identity if self.identity else ""},
expression_index: {self.expression_index if self.expression_index else ""},
source: {self.source if self.source else ""},
message: {self.message},"""
        string = f"""{string}
line: {self.line_count if self.line_count is not None else ""},
scan: {self.scan_count if self.scan_count else ""},
match: {self.match_count if self.match_count else ""}
"""
        return string
