import unittest
import pytest
from lark.exceptions import VisitError
from csvpath.csvpath import CsvPath
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.util.exceptions import MatchException
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestVariables(unittest.TestCase):
    def test_function_variable_bool_tracking(self):
        path = CsvPath()
        Save._save(path, "test_function_variable_bool_tracking")
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
        path.config.csvpath_errors_policy = ["raise"]
        Save._save(path, "test_function_access_variable_tracking_values")
        path.parse(
            f"""${PATH}[*]
                            [
                                tally(#lastname)
                                @ah.so = #firstname
                                @hmmm = @tally_lastname.Bat
                                @ohhh = @hmmm.fish
                                @tally_lastname.Bat = "fred"
                                @tl = total_lines()
                                no()
                            ]
                   """
        )
        # was:  last() -> @lastname.Bat = "fred"
        with pytest.raises(MatchException):
            path.collect()
            print(
                f"test_function_access_variable_tracking_values: path vars: {path.variables}"
            )
            assert path.variables["tally_lastname"]["Bat"] == "fred"
            assert path.variables["hmmm"] == 7
            assert path.variables["ohhh"] is None
            assert path.variables["ah"]["so"]

    def test_variable_names(self):
        path = CsvPath()
        Save._save(path, "test_variable_names")
        path.parse(
            f"""${PATH}[*][
                @a = "a"
                @b.asbool = "qualifier"
                ~ b.asbool and b.asbool.onchange are the same thing
                  but with different runtime behaviors. redefining
                  this way could certainly become a bug in a csvpath,
                  but it is not a bug for the way variables work. ~
                @b.asbool.onchange = "2 qualifiers"
                @c_is_my_name = "underscores"
                @_hmm = "starts with underscore"
                @123me = "starts with number"
                @3.3 = "number and number qualifier"
                @Iam_capped = "capitalization"
                ~@commented = "not here!"~
            ]"""
        )
        path.fast_forward()
        print(f"test_variable_names: path vars: {path.variables}")
        assert "3" in path.variables
        assert "3" in path.variables["3"]
        for i, k in enumerate(path.variables):
            print(f"{i}: {k} = {path.variables[k]}")
        assert len(path.variables) == 7

    def test_variable_bad_names(self):
        path = CsvPath()
        with pytest.raises(VisitError):
            path.parse(
                f"""${PATH}[*][
                    @.hidden = "not really hidden. just starts with period."
                ]"""
            )
            path.fast_forward()
        print("test_variable_bad_names: done")
