import os
import unittest
import pytest
from lark.exceptions import VisitError
from csvpath import CsvPaths
from csvpath.matching.productions import Reference
from csvpath.matching.util.exceptions import MatchException
from tests.csvpaths.builder import Builder

NAMED_FILES_DIR = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files"
NAMED_PATHS_DIR = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths"
PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}food.csv"


class TestCsvPathsReferences(unittest.TestCase):
    def test_reference_for_var(self):
        paths = Builder().build()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.config.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.file_manager.add_named_files_from_dir(NAMED_FILES_DIR)
        paths.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        paths.fast_forward_paths(filename="zipcodes", pathsname="zips")

        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.file_manager.add_named_files_from_dir(
            dirname=f"tests{os.sep}test_resources{os.sep}named_files"
        )
        paths.paths_manager.add_named_paths(
            name="t",
            paths=[
                "~validation-mode:raise,print~$[*][@a = $zips.variables.zipcodes.Boston]"
            ],
        )
        paths.fast_forward_paths(pathsname="t", filename="food")
        results = paths.results_manager.get_named_results("t")
        assert len(results) == 1
        assert results[0].csvpath.variables["a"] == "01915"

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
        cs = Builder().build()
        cs.config.add_to_config("errors", "csvpath", "raise, collect, print")
        cs.config.add_to_config("errors", "csvpaths", "raise, collect, print")
        cs.file_manager.add_named_files_from_dir(NAMED_FILES_DIR)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.fast_forward_paths(filename="zipcodes", pathsname="zips")
        rm = cs.results_manager
        resultset = rm.get_named_results("zips")
        assert resultset
        assert len(resultset) == 1
        results = resultset[0]
        rcp = results.csvpath
        rcp.variables
        assert "zipcodes" in rcp.variables
        assert "Boston" in rcp.variables["zipcodes"]

        #
        # now use the tracked variable by reference
        #
        path = cs.csvpath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                ~#food == "Bulgar" ~
                @zip = $zips.variables.zipcodes.Boston

            ]"""
        )
        path.fast_forward()
        assert not path.has_errors()
        assert path.variables["zip"] == "01915"

    def test_reference2(self):
        cs = Builder().build()
        cs.config.add_to_config("errors", "csvpath", "raise, collect, print")
        cs.config.add_to_config("errors", "csvpaths", "raise, collect, print")
        cs.file_manager.add_named_files_from_dir(NAMED_FILES_DIR)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.collect_paths(filename="zipcodes", pathsname="zips")
        rm = cs.results_manager
        resultset = rm.get_named_results("zips")
        assert resultset
        assert len(resultset) == 1
        results = resultset[0]
        rcp = results.csvpath
        assert rcp
        assert results.lines
        assert len(results.lines) > 0
        #
        # now test if the header `points` has any values
        #
        path = cs.csvpath()
        cs.config.add_to_config("errors", "csvpath", "raise, collect, print")
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
        assert path.has_errors() is not True
        assert "zips" in path.variables
        assert isinstance(path.variables["zips"], list)
        assert "empty_zips" in path.variables
        assert path.variables["empty_zips"] is True
        assert "cities" in path.variables
        assert isinstance(path.variables["cities"], list)
        assert "empty_cities" in path.variables
        assert path.variables["empty_cities"] is False

    def test_reference3(self):
        cs = Builder().build()
        cs.config.add_to_config("errors", "csvpath", "raise, collect, print")
        cs.config.add_to_config("errors", "csvpaths", "raise, collect, print")
        cs.file_manager.add_named_files_from_dir(NAMED_FILES_DIR)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.collect_paths(filename="zipcodes", pathsname="zips")

        rm = cs.results_manager
        resultset = rm.get_named_results("zips")
        assert resultset
        assert len(resultset) == 1
        results = resultset[0]
        rcp = results.csvpath
        assert rcp
        assert results.lines
        assert len(results.lines) > 0
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
        cs = Builder().build()
        cs.config.add_to_config("errors", "csvpath", "raise, collect, print")
        cs.config.add_to_config("errors", "csvpaths", "raise, collect, print")
        cs.file_manager.add_named_files_from_dir(NAMED_FILES_DIR)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.collect_paths(filename="food", pathsname="select")
        #
        # now test if we can see both paths by their name & id
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
        assert len(lines) == 1
        assert path.variables["in1"] is False
        assert path.variables["in2"] is True

    def test_reference_find_uuid(self):
        paths = Builder().build()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.config.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.file_manager.add_named_files_from_dir(NAMED_FILES_DIR)
        paths.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        paths.collect_paths(filename="food", pathsname="select")
        #
        # find file uuid four ways. two ways for two types of references vs.
        # named-file names. likewise, two of the four are for uuid methods vs.
        # getting the manifest and looking up the uuid in it.
        #
        uuid = paths.file_manager.get_named_file_uuid(
            name="$select.results.20:last.two"
        )
        assert uuid is not None

        uuid2 = paths.file_manager.get_named_file_uuid(name="food")
        assert uuid == uuid2

        mani = paths.file_manager.get_manifest("food")
        uuid3 = mani[len(mani) - 1]["uuid"]
        assert uuid2 == uuid3
        #
        # notice here we have a ref to a specific file version, but we are getting
        # the whole manifest. it's up to the caller to figure out which item in the
        # file manifest list they want. in this case we want the last item.
        #
        mani2 = paths.file_manager.get_manifest("$food.files.today:last")
        assert mani == mani2
        uuid4 = mani2[len(mani2) - 1]["uuid"]
        assert uuid3 == uuid4
