import unittest
import pytest
import os
from csvpath import CsvPaths
from csvpath.matching.util.exceptions import MatchException
from tests.csvpaths.builder import Builder

PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}test.csv"
FOOD = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}food.csv"
DIR = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths"


class TestCsvPathsFunctionsIn(unittest.TestCase):
    def test_function_new_in5(self):
        paths = Builder().build()
        paths.file_manager.add_named_file(name="food", path=FOOD)
        paths.paths_manager.add_named_paths_from_dir(directory=DIR)

        paths.fast_forward_paths(pathsname="food_lookup", filename="food")

        path = paths.csvpath()

        path.parse(
            f""" ${FOOD}[1*] [
                @food_found = in(#food, $food_lookup.variables.food_names)
            ]
            """
        )
        lines = path.collect()
        assert len(lines) == 10
        assert path.variables["food_found"] is True

    def test_function_new_in7(self):
        paths = Builder().build()

        paths.file_manager.add_named_file(name="food", path=FOOD)
        paths.paths_manager.add_named_paths_from_dir(directory=DIR)
        paths.collect_paths(pathsname="food_lookup", filename="food")

        path = paths.csvpath()
        path.parse(
            f""" ${FOOD}[1*] [
                @food_found = in(#food, $food_lookup.headers.food)
            ]
            """
        )
        lines = path.collect()
        assert len(lines) == 10
        path = None
