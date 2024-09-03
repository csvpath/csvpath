import unittest
import pytest
from lark.exceptions import VisitError
from csvpath import CsvPaths
from csvpath.matching.productions import Reference
from tests.save import Save

NAMED_FILES_DIR = "tests/test_resources/named_files"
NAMED_PATHS_DIR = "tests/test_resources/named_paths"
PATH = "tests/test_resources/food.csv"


class TestReferences(unittest.TestCase):
    def test_get_reference_for_parts(self):
        reference = Reference(matcher=None, name="zipcodes.variables.zipcodes.Boston")
        nameparts = ["zipcodes", "variables", "zipcodes", "Boston"]
        ref = reference._get_reference_for_parts(nameparts)
        assert ref["file"] == "zipcodes"
        assert ref["paths_name"] is None
        assert ref["var_or_header"] == "variables"
        assert ref["name"] == "zipcodes"
        assert ref["tracking"] == "Boston"

        nameparts = ["zipcodes", "apath", "variables", "zipcodes", "Boston"]
        ref = reference._get_reference_for_parts(nameparts)
        assert ref["file"] == "zipcodes"
        assert ref["paths_name"] == "apath"
        assert ref["var_or_header"] == "variables"
        assert ref["name"] == "zipcodes"
        assert ref["tracking"] == "Boston"

        nameparts = ["zipcodes", "apath", "headers", "zipcodes", "Boston"]
        ref = reference._get_reference_for_parts(nameparts)
        assert ref["file"] == "zipcodes"
        assert ref["paths_name"] == "apath"
        assert ref["var_or_header"] == "headers"
        assert ref["name"] == "zipcodes"
        assert ref["tracking"] == "Boston"

        nameparts = ["zipcodes", "apath", "headers", "zipcodes"]
        ref = reference._get_reference_for_parts(nameparts)
        assert ref["file"] == "zipcodes"
        assert ref["paths_name"] == "apath"
        assert ref["var_or_header"] == "headers"
        assert ref["name"] == "zipcodes"
        assert ref["tracking"] is None

    #
    # using a named path, read city zip codes from a named
    # file track the codes by city to $.variables.zipcodes
    # from another csvpath make a reference to
    #     $.variables.zipcodes.Boston
    # use the reference to set a local var. and check it.
    #
    def test_parse_variable_reference1(self):
        #
        # setup the city->zip variable
        #
        cs = CsvPaths()
        cs.files_manager.add_named_files_from_dir(NAMED_FILES_DIR)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.fast_forward_paths(filename="zipcodes", pathsname="zips")
        rm = cs.results_manager
        resultset = rm.get_named_results("zips")
        assert resultset
        assert len(resultset) == 1
        results = resultset[0]
        rcp = results.csvpath
        rcp.variables
        print(f"test_parse_variable_reference1: rcp.variables: {rcp.variables}")
        assert "zipcodes" in rcp.variables
        assert "Boston" in rcp.variables["zipcodes"]

        #
        # now use the tracked variable by reference
        #
        path = cs.csvpath()
        path.parse(
            f"""
            ${PATH}[1*]
            [
                ~#food == "Bulgar" ~
                @zip = $zips.variables.zipcodes.Boston

            ]"""
        )
        path.fast_forward()
        if path.errors:
            print(
                f"test_parse_variable_reference1: there are errors: {len(path.errors)}"
            )
            for error in path.errors:
                print(f"test_parse_variable_reference1: error: {error}")
        assert not path.has_errors()
        print("test_parse_variable_reference1: done with fast forward")
        print(f"test_parse_variable_reference1: variables: {path.variables}")
        assert path.variables["zip"] == "01915"

    def test_parse_variable_reference2(self):
        cs = CsvPaths()
        cs.files_manager.add_named_files_from_dir(NAMED_FILES_DIR)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.collect_paths(filename="zipcodes", pathsname="zips")
        rm = cs.results_manager
        resultset = rm.get_named_results("zips")
        assert resultset
        assert len(resultset) == 1
        results = resultset[0]
        rcp = results.csvpath
        assert rcp
        #
        # now test if the header `points` has any values
        #
        path = cs.csvpath()
        path.parse(
            f"""
            ${PATH}[1]
            [
                @zip = $zips.headers.points
                @cities = $zips.headers.city

            ]"""
        )
        path.fast_forward()
        if path.errors:
            print(
                f"test_parse_variable_reference1: there are errors: {len(path.errors)}"
            )
            for error in path.errors:
                print(f"test_parse_variable_reference1: error: {error}")
        assert path.has_errors() is not True
        print("test_parse_variable_reference1: done with fast forward")
        print(f"test_parse_variable_reference1: variables: {path.variables}")

        assert path.variables["zip"] is False
        assert path.variables["cities"] is True
