import os
from typing import Dict, List, Tuple
from csvpath.util.line_counter import LineCounter
from csvpath.util.line_monitor import LineMonitor
from csvpath.util.cache import Cache
from csvpath.util.exceptions import InputException, FileException


class LinesAndHeadersCacher:
    """@private"""

    def __init__(self, csvpaths=None):
        self.csvpaths = csvpaths
        self.cache = Cache(self.csvpaths)
        self.pathed_lines_and_headers = {}

    def get_new_line_monitor(self, filename: str) -> LineMonitor:
        if filename is None:
            raise ValueError("Filename cannot be None")
        if filename not in self.pathed_lines_and_headers:
            self._find_lines_and_headers(filename)
        lm = self.pathed_lines_and_headers[filename][0]
        lm = lm.copy()
        return lm

    def get_original_headers(self, filename: str) -> List[str]:
        if filename not in self.pathed_lines_and_headers:
            self._find_lines_and_headers(filename)
        return self.pathed_lines_and_headers[filename][1][:]

    def _find_lines_and_headers(self, filename: str) -> None:
        if filename is None:
            raise ValueError("Filename cannot be None")
        lm, headers = self._cached_lines_and_headers(filename)
        if lm is None or headers is None:
            lc = LineCounter(self.csvpaths)
            lm, headers = lc.get_lines_and_headers(filename)
            self._cache_lines_and_headers(filename, lm, headers)
        self.pathed_lines_and_headers[filename] = (lm, headers)

    def _cached_lines_and_headers(self, filename: str) -> Tuple[LineMonitor, List[str]]:
        if filename is None:
            raise ValueError("Filename cannot be None")
        lm = LineMonitor()
        json = self.cache.cached_text(filename, "json")
        if json is not None and not json.strip() == "":
            lm.load(json)
        else:
            return (None, None)
        headers = self.cache.cached_text(filename, "csv")
        return (lm, headers)

    def _cache_lines_and_headers(
        self, filename, lm: LineMonitor, headers: List[str]
    ) -> None:
        jstr = lm.dump()
        self.cache.cache_text(filename, "json", jstr)
        self.cache.cache_text(filename, "csv", ",".join(headers))
