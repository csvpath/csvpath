import unittest
import pytest
from lark.exceptions import VisitError
from csvpath.csvpath import CsvPaths
from csvpath.matching.util.exceptions import ChildrenException
from csvpath.matching.util.expression_utility import ExpressionUtility
from tests.save import Save

FILES = "tests/test_resources/named_files"
NAMED_PATHS_DIR = "tests/test_resources/named_paths"


class TestReferences(unittest.TestCase):
    def test_parse_variable_reference1(self):
        #
        # does a reference in an assignment parse?
        #
        cs = CsvPaths()
        cs.files_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(NAMED_PATHS_DIR)
        cnt = 0
        for line in cs.next_by_line(filename="food", pathsname="many"):
            cnt += 1
            print(f"vars 0: {cs.current_matchers[0].variables}")
            print(f"vars 1: {cs.current_matchers[1].variables}")
            assert (
                cs.current_matchers[0].variables["test"]
                != cs.current_matchers[1].variables["test"]
            )
        assert cnt == 11
        valid = cs.path_results_manager.is_valid("many")
        assert valid
        assert cs.path_results_manager.get_number_of_results("many") == 2
        pvars = cs.path_results_manager.get_variables("many")
        assert "one" in pvars
        assert isinstance(pvars["one"], int)
        assert pvars["one"] == 11

    def test_parse_header_reference1(self):
        #
        # does a reference in an assignment parse?
        #
        path = CsvPaths()
        path.fast_forward()
