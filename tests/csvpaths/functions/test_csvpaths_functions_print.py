import unittest
import pytest
import logging
import os
from io import StringIO as buffer
from csvpath import CsvPaths
from csvpath.util.log_utility import LogUtility
from csvpath.util.printer import LogPrinter
from csvpath.util.printer import TestPrinter
from csvpath.matching.functions.print.printf import Print, PrintParser
from csvpath.matching.util.lark_print_parser import (
    LarkPrintParser,
    LarkPrintTransformer,
)
from csvpath.matching.util.exceptions import PrintParserException

PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}test.csv"
DIR_FILES = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files"
DIR_PATHS = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths"


class TestCsvPathsFunctionsPrint(unittest.TestCase):
    def test_print_get_runtime_data_from_results(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.file_manager.add_named_files_from_dir(DIR_FILES)
        paths.paths_manager.add_named_paths_from_dir(directory=DIR_PATHS)
        paths.collect_paths(filename="food", pathsname="food")
        results = paths.results_manager.get_named_results("food")
        parser = PrintParser()
        d = results[1].csvpath.delimiter
        q = results[1].csvpath.quotechar
        assert len(results) == 2
        with pytest.raises(PrintParserException):
            results[1].csvpath.config.csvpath_errors_policy = ["raise"]
            results[1].csvpath.delimiter = "#"
            parser._get_runtime_data_from_results(None, results)
        with pytest.raises(PrintParserException):
            results[1].csvpath.config.csvpath_errors_policy = ["raise"]
            results[1].csvpath.quotechar = "#"
            parser._get_runtime_data_from_results(None, results)
        results[1].csvpath.delimiter = d
        results[1].csvpath.quotechar = q
        data = parser._get_runtime_data_from_results(None, results)
        assert isinstance(data["file_name"], str)
        data2 = parser._get_runtime_data_from_results(None, [results[0]])
        assert data["lines_time"] > data2["lines_time"]
        assert "candy check" in data["count_lines"]
        assert data["count_lines"]["candy check"] != data["count_lines"]["first type"]
        assert "candy check" in data["line_number"]
        assert data["line_number"]["candy check"] != data["line_number"]["first type"]
        assert "candy check" in data["count_matches"]
        assert (
            data["count_matches"]["candy check"] != data["count_matches"]["first type"]
        )
        assert "candy check" in data["count_scans"]
        assert data["count_scans"]["candy check"] != data["count_scans"]["first type"]
        assert "candy check" in data["scan_part"]
        assert data["scan_part"]["candy check"] != data["scan_part"]["first type"]
        assert "candy check" in data["match_part"]
        assert data["match_part"]["candy check"] != data["match_part"]["first type"]
        assert "candy check" in data["last_line_time"]
        assert (
            data["last_line_time"]["candy check"]
            != data["last_line_time"]["first type"]
        )
        assert isinstance(data["total_lines"], int)
        assert data["total_lines"] == 11
        assert "candy check" in data["headers"]
        assert isinstance(data["headers"]["candy check"], list)
        assert len(data["headers"]["candy check"]) == 5
        assert "candy check" in data["valid"]
        assert isinstance(data["valid"]["candy check"], bool)
        assert data["valid"]["candy check"] is False
        assert data["valid"]["candy check"] != data["valid"]["first type"]
        assert "candy check" in data["stopped"]
        assert isinstance(data["stopped"]["candy check"], bool)
        assert data["stopped"]["candy check"] is True
        assert data["stopped"]["candy check"] == data["stopped"]["first type"]

    def test_print_header_ref(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.file_manager.add_named_files_from_dir(DIR_FILES)
        paths.paths_manager.add_named_paths_from_dir(directory=DIR_PATHS)
        paths.collect_paths(filename="food", pathsname="food")
        results = paths.results_manager.get_named_results("food")
        parser = PrintParser()
        data: dict = parser._get_headers(None, results)
        assert len(data) == 2
        assert "candy check" in data
        assert len(data["candy check"]) == 5

    def test_print_parser_named_paths_data(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        LogUtility.logger(paths, "debug")
        paths.file_manager.add_named_files_from_dir(DIR_FILES)
        paths.paths_manager.add_named_paths_from_dir(directory=DIR_PATHS)
        paths.fast_forward_paths(pathsname="food", filename="food")
        path = paths.csvpath()
        LogUtility.logger(path, "debug")
        pathstr = f"""
            ~ name: test path
              description: a way of checking things ~
            ${PATH}[*] [ yes() ]"""
        path.parse(pathstr)
        path.collect()
        parser = PrintParser(path)
        printstr = """ $food.variables.type """
        result = parser.transform(printstr)
        assert result.strip() == "fruit"
        printstr = """ $food.metadata.name """
        result = parser.transform(printstr)
        assert result and result.strip() in ["candy check", "first type"]
