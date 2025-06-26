import unittest
import os
from csvpath import CsvPaths
from tests.csvpaths.builder import Builder


class TestCsvPathsSingleFromGroup(unittest.TestCase):
    def test_single_from_group(self):
        paths = Builder().build()
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.file_manager.add_named_file(
            name="food",
            path=f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files{os.sep}food.csv",
        )
        paths.paths_manager.add_named_paths_from_dir(
            directory=f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths"
        )
        paths.fast_forward_paths(pathsname="$many.csvpaths.many_two", filename="food")
        vars = paths.results_manager.get_variables("$many.csvpaths.many_two")
        #
        # note from point in time pre-reference grammar
        #
        # longer term, # is still available as a separator within reference components,
        # other than in datatype. its very possible that a more compelling new use will
        # come to light.
        #
        # paths.fast_forward_paths(pathsname="many#many_two", filename="food")
        # vars = paths.results_manager.get_variables("many#many_two")
        assert "two" in vars
        assert "one" not in vars
