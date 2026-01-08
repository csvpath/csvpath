import unittest
import pytest
import os
import textwrap
from csvpath import CsvPath
from csvpath.matching.functions.function_factory import FunctionFactory
from csvpath.util.class_loader import ClassLoader
from csvpath.matching.util.exceptions import ChildrenException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
CPATH = os.path.join(
    "tests",
    "csvpath",
    "examples",
    "csvpath_examples_custom_func",
    "extra-functions.imports",
)

CPATH2 = os.path.join(
    "tests",
    "csvpath",
    "examples",
    "csvpath_examples_custom_func",
    "extra-functions-2.imports",
)


class TestCsvpathExamplesCustomFunc(unittest.TestCase):
    def test_csvpath_examples_custom_func_1(self):
        path = CsvPath()
        path.config.add_to_config("functions", "imports", CPATH)
        #
        # this test isn't really about custom functions, it is about passing arguments that
        # aren't expected. a problem came up during these tests, so I'm testing the fix here.
        # see Args ~410
        #
        path.parse(f"${PATH}[3][ @e = A(@1, #2) ]")
        with pytest.raises(ChildrenException):
            path.fast_forward()

    def test_csvpath_examples_custom_func_2(self):
        #
        # clear external functions
        #
        FunctionFactory.NOT_MY_FUNCTION = {}
        path = CsvPath()
        if not os.path.exists(CPATH):
            raise RuntimeError(f"{CPATH} must exist")

        path.config.add_to_config("functions", "imports", CPATH)
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

    def test_different_output_same_name(self) -> None:
        #
        # clear external functions
        #
        FunctionFactory.NOT_MY_FUNCTION = {}
        path = CsvPath(project="A", project_context="a1")
        path.config.add_to_config("functions", "imports", CPATH)
        path.parse(f"${PATH}[3][ @e = A() ]")
        path.fast_forward()
        vars1 = path.variables
        assert "e" in vars1
        assert vars1["e"] is True

        path = CsvPath(project="B", project_context="b2")
        path.config.add_to_config("functions", "imports", CPATH2)
        path.parse(f"${PATH}[3][ @e = A() ]")
        path.fast_forward()
        vars2 = path.variables
        assert "e" in vars2
        assert vars2["e"] == "?"
