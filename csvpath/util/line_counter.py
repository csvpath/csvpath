import csv
import time
import os
from typing import List, Any
from csvpath.util.line_monitor import LineMonitor
from .file_readers import DataFileReader


class LineCounter:
    """CsvPath and FilesManager uses the line counter to find the total number of lines
    and the first data line to use as headers.
    """

    #
    # csvpathx can be either CsvPath or CsvPaths
    #
    def __init__(self, csvpathx) -> None:
        # just need quotechar, delimiter, and logger
        self.csvpathx = csvpathx

    def get_lines_and_headers(self, path: str) -> tuple[LineMonitor, List[Any]]:
        lm = LineMonitor()
        headers = None
        start = time.time()
        lm.reset()
        with DataFileReader(
            path, delimiter=self.csvpathx.delimiter, quotechar=self.csvpathx.quotechar
        ) as reader:
            for line in reader.next():
                lm.next_line(last_line=[], data=line)
                if len(line) == 0 and self.csvpathx.skip_blank_lines:
                    continue
                #
                # some data formats embed headers in each line -- e.g. JSONL.
                # in that case, we never have a header line. we'll just take the
                # first headers available. in JSONL headers are an even looser
                # concept than in CSV. it is very possible that a JSONL file's
                # headers never settle for more than one line.
                #
                if reader.updates_headers and reader.current_headers:
                    line = reader.current_headers
                if (not headers or len(headers) == 0) and line and len(line) > 0:
                    headers = line[:]
        if not headers:
            headers = []
        headers = LineCounter.clean_headers(headers)
        end = time.time()
        self.csvpathx.logger.info("Lines and headers took %s", round(end - start, 2))
        lm.set_end_lines_and_reset()
        return (lm, headers)

    @classmethod
    def clean_headers(self, headers: List[str]) -> List[str]:
        hs = []
        for header in headers:
            header = header.strip()
            header = header.replace(";", "")
            header = header.replace(",", "")
            header = header.replace("|", "")
            header = header.replace("\t", "")
            header = header.replace("`", "")
            hs.append(header)
        return hs
