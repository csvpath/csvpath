import unittest
import pytest
from lark.exceptions import VisitError
from csvpath import CsvPaths, CsvPath
from csvpath.matching.productions import Reference
from csvpath.matching.util.exceptions import MatchException, ChildrenException
from tests.save import Save

NAMED_FILES_DIR = "tests/test_resources/named_files"
NAMED_PATHS_DIR = "tests/test_resources/named_paths"
PATH = "tests/test_resources/food.csv"


class TestReferences(unittest.TestCase):
    def test_reference_for_parts(self):
        reference = Reference(matcher=None, name="zipcodes.variables.zipcodes.Boston")
        nameparts = ["zipcodes", "variables", "zipcodes", "Boston"]
        ref = reference._get_reference_for_parts(nameparts)
        assert ref["paths_name"] == "zipcodes"
        assert ref["var_or_header"] == "variables"
        assert ref["name"] == "zipcodes"
        assert ref["tracking"] == "Boston"

        nameparts = ["zipcodes", "headers", "zipcodes"]
        ref = reference._get_reference_for_parts(nameparts)
        assert ref["paths_name"] == "zipcodes"
        assert ref["var_or_header"] == "headers"
        assert ref["name"] == "zipcodes"
        assert ref["tracking"] is None

    def test_reference_for_wrong_parts(self):
        reference = Reference(matcher=None, name="zipcodes.variables.zipcodes.Boston")
        nameparts = ["zipcodes", "metadata", "zipcodes", "Boston"]
        with pytest.raises(ChildrenException):
            ref = reference._get_reference_for_parts(nameparts)
            assert ref["paths_name"] == "zipcodes"
            assert ref["var_or_header"] == "variables"
            assert ref["name"] == "zipcodes"
            assert ref["tracking"] == "Boston"

    def test_reference_no_csvpaths(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [
                @b = $zips.variables.zipcodes.Boston
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()

    #
    # using a named path, read city zip codes from a named
    # file track the codes by city to $.variables.zipcodes
    # from another csvpath make a reference to
    #     $.variables.zipcodes.Boston
    # use the reference to set a local var. and check it.
    #
    def test_reference1(self):
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

    def test_reference2(self):
        cs = CsvPaths()
        cs.files_manager.add_named_files_from_dir(NAMED_FILES_DIR)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.collect_paths(filename="zipcodes", pathsname="zips")

        rm = cs.results_manager
        resultset = rm.get_named_results("zips")
        print(f"\n test_parse_variable_reference2: resultset: {resultset} ")

        assert resultset
        assert len(resultset) == 1
        results = resultset[0]
        rcp = results.csvpath
        assert rcp
        assert results.lines
        assert len(results.lines) > 0
        print(f"\n test_parse_variable_reference2: lookup lines: {results.lines}")
        #
        # now test if the header `points` has any values
        #
        path = cs.csvpath()
        path.parse(
            f"""
            ${PATH}[1]
            [
                @zips = $zips.headers.points
                @cities = $zips.headers.city
                @empty_zips = empty(@zip)
                @empty_cities = empty(@cities)
            ]"""
        )
        path.fast_forward()
        if path.errors:
            print(
                f"test_parse_variable_reference2: there are errors: {len(path.errors)}"
            )
            for error in path.errors:
                print(f"test_parse_variable_reference1: error: {error}")
        assert path.has_errors() is not True
        print("test_parse_variable_reference2: done with fast forward")
        print(f"test_parse_variable_reference2: variables: {path.variables}")

        assert "zips" in path.variables
        assert isinstance(path.variables["zips"], list)
        assert "empty_zips" in path.variables
        assert path.variables["empty_zips"] is True

        assert "cities" in path.variables
        assert isinstance(path.variables["cities"], list)
        assert "empty_cities" in path.variables
        assert path.variables["empty_cities"] is False

    def test_reference3(self):
        cs = CsvPaths()
        cs.files_manager.add_named_files_from_dir(NAMED_FILES_DIR)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.collect_paths(filename="zipcodes", pathsname="zips")

        rm = cs.results_manager
        resultset = rm.get_named_results("zips")
        print(f"\n test_parse_variable_reference3: resultset: {resultset} ")

        assert resultset
        assert len(resultset) == 1
        results = resultset[0]
        rcp = results.csvpath
        assert rcp
        assert results.lines
        assert len(results.lines) > 0
        print(f"\n test_parse_variable_reference3: lookup lines: {results.lines}")
        #
        #
        #
        path = cs.csvpath()
        path.parse(
            f"""
            ${PATH}[1]
            [
                @b = $zips.variables.zipcodes.Boston
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1

        path = cs.csvpath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                ~ Boston always exists in the reference so all match ~
                $zips.variables.zipcodes.Boston
                print.nocontrib("199:  : :: boston: $zips.variables.zipcodes.Boston ")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 11

        path = cs.csvpath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                ~ we cannot match on Salem so no matches ~
                $zips.variables.zipcodes.Salem
                @l = length( $zips.variables.zipcodes.Boston )
                print(" $.variables.l: boston: $zips.variables.zipcodes.Boston ")
            ]"""
        )
        lines = path.collect()
        print(f"\n test_reference3: path.vars: {path.variables}")
        assert len(lines) == 0
        assert "l" in path.variables
        assert path.variables["l"] > 0

    #
    # this test separates path results by a metadata field.
    # it matches a tracking value on a header to the id or name
    # of the path in the metadata.
    #
    # e.g. $x.headers.y.z means look at the headers of
    # named-paths x and use z to pick out just one of those
    # x paths so that we can return a specific set of header
    # values
    #
    # in a future iteration I could imagine this changing to
    # something like $x[z].headers.y which would be more
    # general. but its not a priority for today.
    #
    def test_reference_specific_header_lookup(self):
        cs = CsvPaths()
        cs.files_manager.add_named_files_from_dir(NAMED_FILES_DIR)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.collect_paths(filename="food", pathsname="select")
        #
        # now test if we can see both paths by their name/id
        #
        path = cs.csvpath()
        path.parse(
            f"""
            ${PATH}[1]
            [
                @in1 = in( "Apple", $select.headers.food.one )
                @in2 = in( "Apple", $select.headers.food.two )
            ]"""
        )
        lines = path.collect()
        print(f"test_parse_variable_reference4: vars: {path.variables}")
        assert len(lines) == 1

        assert path.variables["in1"] is False
        assert path.variables["in2"] is True
