import unittest
from csvpath import CsvPath, CsvPaths
from tests.save import Save
from csvpath.matching.functions.print.jinjaf import Jinjaf

PATH = "tests/test_resources/test.csv"
NAMED_FILES_DIR = "tests/test_resources/named_files"
NAMED_PATHS_DIR = "tests/test_resources/named_paths"


class TestJinja(unittest.TestCase):
    def test_function_jinja_get_tokens(self):
        cs = CsvPaths()
        cs.files_manager.add_named_files_from_dir(NAMED_FILES_DIR)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.fast_forward_paths(filename="zipcodes", pathsname="zips")
        rm = cs.results_manager
        resultset = rm.get_named_results("zips")
        results = resultset[0]
        rcp = results.csvpath
        rcp.variables
        print(f"test_parse_variable_reference1: rcp.variables: {rcp.variables}")
        #
        #
        #
        path = cs.csvpath()
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
        print(f"test_function_jinja_get_tokens: tokens: {tokens}")
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

        assert tokens["local"]["csvpath"]["file_name"] == PATH
        assert isinstance(tokens["zips"]["headers"], dict)
        for z in tokens["zips"]:
            print(f"\n test_function_jinja_get_tokens: z: {z}")
            for k, v in tokens["zips"][z].items():
                print(f"    {k} = {v}")
        #
        # zip's last line is blank. atm we don't offer a way to roll
        # up a line. if we want to add a line index capability or something
        # this can come back.
        #
        # assert tokens["zips"]["headers"]["zip"] == "66086"
        assert tokens["zips"]["headers"]["zip"] == ""

    def test_function_jinja1(self):
        paths = CsvPaths()
        out = "tests/test_resources/out.txt"
        inf = "tests/test_resources/in.txt"

        path = paths.csvpath()
        Save._save(path, "test_function_jinja")
        path.parse(
            f""" ${PATH}[*][ yes()
                             @name = "turtle"
                             last.nocontrib() -> jinja("{inf}", "{out}")
            ]
            """
        )
        print("")
        path.fast_forward()
        print(f"test_function_jinja: path vars: {path.variables}")
        with open(out, "r") as file:
            txt = file.read()
            print(f"test_function_jinja1: created output text: \n{txt}")
            i = txt.find("scan count: 9")
            assert i >= 0