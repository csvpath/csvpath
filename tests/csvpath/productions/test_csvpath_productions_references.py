import os
import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.productions import Reference
from csvpath.matching.util.exceptions import MatchException

NAMED_FILES_DIR = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}named_files"
NAMED_PATHS_DIR = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}named_paths"
PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}food.csv"


class TestCsvPathProductionsReferences(unittest.TestCase):
    def test_reference_for_parts(self):
        reference = Reference(matcher=None, name="zipcodes.variables.zipcodes.Boston")
        nameparts = ["zipcodes", "variables", "zipcodes", "Boston"]
        ref = reference._get_reference_for_parts(nameparts)
        assert ref["paths_name"] == "zipcodes"
        assert ref["data_type"] == "variables"
        assert ref["name"] == "zipcodes"
        assert ref["tracking"] == "Boston"

        nameparts = ["zipcodes", "headers", "zipcodes"]
        ref = reference._get_reference_for_parts(nameparts)
        assert ref["paths_name"] == "zipcodes"
        assert ref["data_type"] == "headers"
        assert ref["name"] == "zipcodes"
        assert ref["tracking"] is None

    def test_reference_csvpaths_data_type(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["raise"]
        path.parse(
            f"""
            ${PATH}[1]
            [
                @ref = $zips.csvpaths.zipcodes
            ]"""
        )
        path.collect()

    def test_reference_no_csvpaths(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["raise"]
        path.parse(
            f"""
            ${PATH}[1]
            [
                @b = $zips.variables.zipcodes.Boston
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()
