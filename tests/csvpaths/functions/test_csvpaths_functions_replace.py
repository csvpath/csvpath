import unittest
import pytest
import os
from csvpath import CsvPaths
from tests.csvpaths.builder import Builder

FILE = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}test.csv"
PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}insert.csvpath"


class TestCsvPathsFunctionsReplace(unittest.TestCase):
    def test_function_insert_2(self):
        paths = Builder().build()

        paths.paths_manager.add_named_paths_from_file(name="insert", file_path=PATH)
        paths.file_manager.add_named_file(name="insert", path=FILE)
        paths.collect_paths(pathsname="insert", filename="insert")
        results = paths.results_manager.get_named_results("insert")

        assert len(results) == 2
        result = results[1]
        assert len(result) == 8
