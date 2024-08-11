import unittest
from csvpath.matching.functions.function_factory import FunctionFactory
from csvpath.csvpath import CsvPath
from csvpath.matching.matcher import Matcher
from csvpath.matching.expression_utility import ExpressionUtility

PATH = "tests/test_resources/test.csv"


class TestFunctionsVariables(unittest.TestCase):
    def test_function_access_tracking_values(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*]
                            [
                                tally(#lastname)
                                @ah.so = #firstname
                                @hmmm = @lastname.Bat
                                @ohhh = @hmmm.fish
                                last() -> @lastname.Bat = "fred"
                                @tl = total_lines()
                                no()
                            ]
                   """
        )
        path.collect()
        print(f"test_function_access_tracking: path vars: {path.variables}")
        assert path.variables["lastname"]["Bat"] == "fred"
        assert path.variables["hmmm"] == 7
        assert path.variables["ohhh"] is None
        assert path.variables["ah"]["so"]
