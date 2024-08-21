import unittest
import pytest
from lark.exceptions import VisitError
from csvpath.csvpath import CsvPath
from csvpath.matching.util.exceptions import ChildrenException
from csvpath.matching.util.expression_utility import ExpressionUtility
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestReferences(unittest.TestCase):
    def test_reference1(self):
        #
        # does a reference in an assignment parse?
        #
        path = CsvPath()
        Save._save(path, "test_reference1")
        path.parse(
            f"""${PATH}
                        [*]
                        [
                            count.t()
                            @a = $ref.headers.zipcodes
                        ]
                   """
        )
        path.fast_forward()
        print(f"test_function_variable_bool_tracking: path vars: {path.variables}")
