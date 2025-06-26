import unittest
import pytest
import os
from csvpath import CsvPaths
from csvpath.util.printer import LogPrinter
from csvpath.matching.util.exceptions import MatchException
from tests.csvpaths.builder import Builder

PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathsComments(unittest.TestCase):
    def test_comment_settings_affecting_multiple_paths(self):
        paths = Builder().build()
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        """~ 3 paths:
                - AND no matches all returned
                - OR all match all returned
                - AND no matches none returned
                - OR all match none returned
        ~"""
        paths.file_manager.add_named_file(name="test", path=PATH)
        settings = {}
        settings["settings"] = [
            """~ logic-mode:AND return-mode:no-matches print-mode:default ~ $[1][ yes() no() print("Hi $.csvpath.line_number")]""",
            """~ logic-mode:OR return-mode:matches print-mode:default  ~ $[2][ yes() no() print("Hi $.csvpath.line_number")]""",
            """~ logic-mode:AND return-mode:matches print-mode:no-default  ~ $[3][ yes() no() print("Hi $.csvpath.line_number")]""",
            """~ logic-mode:OR return-mode:no-matches print-mode:no-default ~ $[4][ yes() no() print("Hi $.csvpath.line_number")]""",
        ]
        paths.paths_manager.set_named_paths(settings)
        paths.collect_paths(filename="test", pathsname="settings")
        results = paths.results_manager.get_named_results("settings")
        assert len(results) == 4
        assert len(results[0]) == 1
        # results has 1 line that was printed by print()
        # results[0].csvpath handed that 1 line off to two printers: StdOut and the Result
        assert results[0].lines_printed < len(results[0].csvpath.printers)
        assert len(results[1]) == 1
        assert results[1].lines_printed < len(results[1].csvpath.printers)
        assert len(results[2]) == 0
        # the print mode removes StdOut from results[2].csvpath leaving 1 printer, Result
        assert results[2].lines_printed == len(results[2].csvpath.printers)
        assert len(results[3]) == 0
        assert results[3].lines_printed == len(results[3].csvpath.printers)
