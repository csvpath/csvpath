from typing import Dict, List, Tuple
import json
from csvpath.util.line_counter import LineCounter
from csvpath.util.line_monitor import LineMonitor
from csvpath.util.cache import Cache


class LinesAndHeadersCacher:

    #
    # csvpathx can be either CsvPath or CsvPaths
    #
    def __init__(self, csvpathx=None):
        self.csvpathx = csvpathx
        self.cache = Cache(self.csvpathx)

    def get_new_line_monitor(self, filename: str) -> LineMonitor:
        if filename is None:
            raise ValueError("Filename cannot be None")
        lm, headers = self._find_lines_and_headers(filename)
        return lm.copy()

    def get_original_headers(self, filename: str) -> List[str]:
        lm, headers = self._find_lines_and_headers(filename)
        return headers[:]

    def _find_lines_and_headers(self, filename: str) -> None:
        if filename is None:
            raise ValueError("Filename cannot be None")
        lm, headers = self._cached_lines_and_headers(filename)
        if lm is None or headers is None:
            lc = LineCounter(self.csvpathx)
            lm, headers = lc.get_lines_and_headers(filename)
            self._cache_lines_and_headers(filename, lm, headers)
        return lm, headers

    def _cached_lines_and_headers(self, filename: str) -> Tuple[LineMonitor, List[str]]:
        if filename is None:
            raise ValueError("Filename cannot be None")
        lm = LineMonitor()
        jjson = self.cache.cached_text(filename)
        if jjson is None:
            return (None, None)
        #
        # bit of goofy json sneezing :/
        #
        js = json.loads(jjson)
        headers = js.get("headers")
        headers = None if headers is None else headers[:]
        del js["headers"]
        jjson = json.dumps(js)
        lm.load(jjson)
        return (lm, headers)

    def _cache_lines_and_headers(
        self, filename, lm: LineMonitor, headers: List[str]
    ) -> None:
        js = lm.dump()
        jjson = json.loads(js)
        jjson["headers"] = headers
        js = json.dumps(jjson)
        self.cache.cache_text(filename, js)
