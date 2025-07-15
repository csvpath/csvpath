import unittest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsAnd(unittest.TestCase):
    def test_function_and_1(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*][
                ~ count.houses counts all values of and(), regardless
                  of match, so it tracks True and False in @houses.
                  we end on a Frog Bat so c ends at 2 ~
                @c = count.houses(
                        and(
                            #firstname == "Frog",
                            #lastname == "Bat"
                        )
                    )
                ~ count.cars() only counts matches. c2 is 2 because of the
                  number of matches, not the match or line we end on, because
                  we only match when and() is True. we don't see the match
                  count in the vars because it is a global (within the
                  CsvPath) accessible to us elsewhere ~
                @c2 = count.cars()
                and(
                            #firstname == "Frog",
                            #lastname == "Bat"
                )

            ]"""
        )
        lines = path.collect()
        assert "c" in path.variables
        assert path.variables["c2"] == 2
        assert len(lines) == 2

    def test_function_and_2(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[1*][
                and( yes(), yes() ) ->
                    @check1 = true()
                and( yes(), no() ) ->
                    @check2 = true()
                and( yes(), last() ) ->
                    @check3 = true()
                and( yes(), last() ) ->
                    push("check3s", @check3)
            ]"""
        ).fast_forward()

        assert "check1" in path.variables
        assert "check2" not in path.variables
        assert "check3" in path.variables
        assert "check3s" in path.variables

        assert path.variables["check1"] is True
        assert path.variables["check3"] is True
        assert len(path.variables["check3s"]) == 1
