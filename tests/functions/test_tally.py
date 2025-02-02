import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"


class TestFunctionsTally(unittest.TestCase):
    def test_function_tally1(self):
        path = CsvPath()
        path.parse(f"${PATH}[*][tally(#lastname) no()] ")
        path.collect()
        assert path.variables["tally_lastname"]["Bat"] == 7

    def test_function_tally2(self):
        path = CsvPath()
        path.parse(f"${PATH}[*][tally(#firstname, #lastname)] ")
        path.collect()
        assert path.variables["tally"]["Frog|Bat"] == 2

    def test_function_tally3(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*][
                            or( #firstname == "Frog", #firstname == "Ants" )
                            tally.sothere.onmatch(#firstname, #lastname)
                        ]
                    """
        )
        path.collect()
        assert path.variables["sothere"]["Frog|Bat"] == 2
        assert len(path.variables["sothere_firstname"]) == 2

    def test_function_tally4(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["raise"]
        path.parse(
            f"""${PATH}[*]
                            [
                                tally(#lastname) no()
                                @hmmm = @lastname.Bat
                                @ohhh = @hmmm.fish
                                @tally_lastname.Bat = "fred"
                            ]
                   """
        )
        path.logger.warning("We are going to intentionally raise an exception")
        with pytest.raises(MatchException):
            path.collect()
            assert path.variables["lastname"]["Bat"] == "fred"
            assert path.variables["hmmm"] == 7
            assert path.variables["ohhh"] is None
