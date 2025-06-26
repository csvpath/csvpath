import unittest
import os
from csvpath import CsvPaths
from csvpath.matching.functions.print.jinjaf import Jinjaf
from csvpath.util.path_util import PathUtility as pathu
from tests.csvpaths.builder import Builder

PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}test.csv"
NAMED_FILES_DIR = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files"
NAMED_PATHS_DIR = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths"
OUT = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}out.txt"
IN = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}in.txt"


class TestCsvPathsFunctionsJinja(unittest.TestCase):
    def test_function_jinja_get_tokens(self):
        paths = Builder().build()
        paths.file_manager.add_named_files_from_dir(NAMED_FILES_DIR)
        paths.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        paths.fast_forward_paths(filename="zipcodes", pathsname="zips")
        rm = paths.results_manager
        resultset = rm.get_named_results("zips")
        results = resultset[0]
        rcp = results.csvpath
        rcp.variables
        path = paths.csvpath()
        path.parse(
            f"""
            ${PATH}[1*]
            [
                @fish = "bluefish"
                @zip = $zips.variables.zipcodes.Boston

            ]"""
        )
        path.fast_forward()
        jinja = Jinjaf(path.matcher, name="testing")
        tokens = jinja._get_tokens(["zips"])
        assert tokens
        assert "zips" in tokens
        assert "local" in tokens
        assert "metadata" in tokens["zips"]
        assert "headers" in tokens["zips"]
        assert "csvpath" in tokens["zips"]
        assert "variables" in tokens["zips"]

        assert tokens["local"]["variables"]["fish"] == "bluefish"
        assert isinstance(tokens["zips"]["variables"]["zipcodes"], dict)
        assert tokens["zips"]["variables"]["zipcodes"]["Boston"] == "01915"

        assert pathu.equal(tokens["local"]["csvpath"]["file_name"], PATH)
        assert isinstance(tokens["zips"]["headers"], dict)
        #
        # zip's last line is blank. atm we don't offer a way to roll
        # up a line. if we want to add a line index capability or something
        # this can come back.
        #
        # assert tokens["zips"]["headers"]["zip"] == "66086"
        assert tokens["zips"]["headers"]["zip"] == ""

    def test_function_jinja1(self):
        paths = Builder().build()
        path = paths.csvpath()
        path.parse(
            f""" ~name:jinja~ ${PATH}[*][ yes()
                             @name = "turtle"
                             last.nocontrib() -> jinja("{IN}", "{OUT}")
            ]
            """
        )
        path.fast_forward()
        with open(OUT, "r") as file:
            txt = file.read()
            i = txt.find("scan count: 9")
            assert i >= 0
