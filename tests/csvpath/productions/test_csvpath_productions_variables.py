import os
import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.util.exceptions import ChildrenException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathProductionsVariables(unittest.TestCase):
    def test_function_variable_asbool(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(
            f"""${PATH}[1][
                    push("a", "")
                    pop("a")
                    @c1 = @a.asbool

                    push("a", "")
                    @c2 = @a.asbool

                    put("b")
                    @c3 = @b.asbool
                    put("b", "c", "d")
                    @c4 = @b.asbool

                    @b = ""
                    @c5 = @b.asbool
                    @b = "6"
                    @c6 = @b.asbool

                    @b = 1
                    @c7 = @b.asbool
                    @b = 0
                    @c8 = @b.asbool

                    @b = yes()
                    @c9 = @b.asbool
                    @b = no()
                    @c10 = @b.asbool

                    @b = "true"
                    @c11 = @b.asbool
                    @b = "false"
                    @c12 = @b.asbool

                    @b = now()
                    @c13 = @b.asbool

                    @b = none()
                    @c14 = @b.asbool

                ]
            """
        )
        path.fast_forward()
        assert path.variables.get("c1") is False
        assert path.variables.get("c2") is True
        assert path.variables.get("c3") is False
        assert path.variables.get("c4") is True
        assert path.variables.get("c5") is False
        assert path.variables.get("c6") is True
        assert path.variables.get("c7") is True
        assert path.variables.get("c8") is False
        assert path.variables.get("c9") is True
        assert path.variables.get("c10") is False
        assert path.variables.get("c11") is True
        assert path.variables.get("c12") is False
        assert path.variables.get("c13") is True
        assert path.variables.get("c14") is False

    def test_function_variable_bool_tracking(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(
            f"""${PATH}[*][
                            count.t(#lastname=="Bat")
                            @u = @t.True
                        ]
                   """
        )
        path.fast_forward()
        assert "u" in path.variables
        assert path.variables["u"] == 7

    def test_function_access_variable_tracking_values(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["raise"]
        path.parse(
            f"""${PATH}[*][
                                tally(#lastname)
                                @ah.so = #firstname
                                @hmmm = @tally_lastname.Bat
                                @ohhh = @hmmm.fish
                                @tally_lastname.Bat = "fred"
                                @tl = total_lines()
                                no()
                     ]"""
        )
        with pytest.raises(MatchException):
            path.collect()
            """
            assert path.variables["tally_lastname"]["Bat"] == "fred"
            assert path.variables["hmmm"] == 7
            assert path.variables["ohhh"] is None
            assert path.variables["ah"]["so"]
            """

    def test_variable_names(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
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
        assert "3" in path.variables
        assert "3" in path.variables["3"]
        assert len(path.variables) == 7

    def test_variable_bad_names(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(
            f"""${PATH}[*][
                @.hidden = "not really hidden. just starts with period."
            ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise,print")
        # with pytest.raises(VisitError):
        with pytest.raises(ChildrenException):
            path.fast_forward()
