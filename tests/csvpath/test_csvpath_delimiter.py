import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.util.printer import LogPrinter
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}bar.csv"


class TestCsvPathDelimiter(unittest.TestCase):
    def test_delimiter_from_metadata(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
            ~
            use-delimiter:pipe
            use-quotechar:tick
            validation-mode: raise, print
            ~
            ${PATH}[1*]
            [
                @h = count_headers()
            ]
            """
        )
        assert path.delimiter == "|"
        assert path.quotechar == "`"
        path.fast_forward()
        print(f"headers: {path.headers}")
        print(f"meta: {path.metadata}")
        print(f"vars: {path.variables}")
        assert "h" in path.variables
        assert path.variables["h"] == 4
        assert path.headers[2] == "other thing"
