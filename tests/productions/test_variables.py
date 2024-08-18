import unittest
from csvpath.csvpath import CsvPath
from csvpath.matching.util.expression_utility import ExpressionUtility

PATH = "tests/test_resources/test.csv"


class TestVariables(unittest.TestCase):
    def test_function_variable_bool_tracking(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}
                        [*]
                        [
                            count.t(#lastname=="Bat")
                            @u = @t.True
                        ]
                   """
        )
        path.fast_forward()
        print(f"test_function_variable_bool_tracking: path vars: {path.variables}")
        assert "u" in path.variables
        assert path.variables["u"] == 7

    def test_function_access_variable_tracking_values(self):
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
