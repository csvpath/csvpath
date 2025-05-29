import unittest
import pytest
import os
from csvpath import CsvPaths
from csvpath.matching.util.exceptions import MatchException
from csvpath.util.file_readers import DataFileReader


class TestSchemas(unittest.TestCase):
    @classmethod
    def setup_class(cls):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.config.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.file_manager.add_named_file(
            name="schemas",
            path=f"tests{os.sep}examples{os.sep}schemas{os.sep}people.csv",
        )
        paths.paths_manager.add_named_paths_from_file(
            name="schemas",
            file_path=f"tests{os.sep}examples{os.sep}schemas{os.sep}schemas.csvpath",
        )

    @classmethod
    def teardown_class(cls):
        ...

    def test_line_schemas_1(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpath", "collect,print")
        paths.config.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.collect_paths(filename="schemas", pathsname="$schemas.csvpaths.one")
        results = paths.results_manager.get_named_results("schemas")
        assert len(results) == 1
        result = results[0]
        assert result.is_valid
        assert result.errors_count == 0

    def test_line_schemas_2(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpath", "collect, print")
        paths.collect_paths(filename="schemas", pathsname="$schemas.csvpaths.two")
        results = paths.results_manager.get_named_results("schemas")
        assert len(results) == 1
        result = results[0]
        assert result.is_valid
        assert result.errors_count == 0

    def test_line_schemas_3(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.collect_paths(filename="schemas", pathsname="$schemas.csvpaths.three")
        results = paths.results_manager.get_named_results("schemas")
        assert len(results) == 1
        result = results[0]
        assert result.is_valid
        assert result.errors_count == 0

    def test_line_schemas_4(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.collect_paths(filename="schemas", pathsname="$schemas.csvpaths.four")
        results = paths.results_manager.get_named_results("schemas")
        assert len(results) == 1
        result = results[0]
        assert result.is_valid
        assert result.errors_count == 0
