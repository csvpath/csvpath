import unittest
import pytest
import os
import textwrap
from csvpath import CsvPath
from csvpath.util.class_loader import ClassLoader
from csvpath.matching.util.exceptions import ChildrenException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvpathExamplesCustomFunc(unittest.TestCase):
    def test_csvpath_examples_custom_func_1(self):
        path = CsvPath()
        path.config.add_to_config(
            "functions",
            "imports",
            os.path.join(
                "tests",
                "csvpath",
                "examples",
                "csvpath_examples_custom_func",
                "extra-functions.imports",
            ),
        )
        #
        # this test isn't really about custom functions, it is about passing arguments that
        # aren't expected. a problem came up during these tests, so I'm testing the fix here.
        # see Args ~410
        #
        path.parse(f"${PATH}[3][ @e = A(@1, #2) ]")
        with pytest.raises(ChildrenException):
            path.fast_forward()

    def test_csvpath_examples_custom_func_2(self):
        path = CsvPath()
        path.config.add_to_config(
            "functions",
            "imports",
            os.path.join(
                "tests",
                "csvpath",
                "examples",
                "csvpath_examples_custom_func",
                "extra-functions.imports",
            ),
        )
        path.parse(f"${PATH}[3][ @e = A() ]")
        path.fast_forward()
        assert "e" in path.variables
        assert path.variables["e"] is True

    def test_no_collision_between_projects(tmp_path):
        temppath_a = os.path.join(
            "tests", "csvpath", "examples", "csvpath_examples_custom_func", "t1"
        )
        temppath_b = os.path.join(
            "tests", "csvpath", "examples", "csvpath_examples_custom_func", "t2"
        )
        name = "Yes"
        stmt = f"from one.yes import {name} as aee"
        a = ClassLoader.load_private_class(temppath_a, stmt, None, "noname")
        b = ClassLoader.load_private_class(temppath_b, stmt, None, "noname")
        assert a
        assert b
        assert type(a) is not type(b)
