import unittest
import os
from csvpath.csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
NUMBERS = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}numbers2.csv"


class TestCsvPathFunctionsMatches(unittest.TestCase):
    def test_function_matches_1(self):
        path = CsvPath()
        path.parse(
            f"""~validation-mode:print,raise~${PATH}[*][
                    #lastname == "Bat"
                    matches() -> counter.bat()
                    @c = count()
                    @c.nocontrib == @bat -> print("sufficient bats")
            ]"""
        )
        path.fast_forward()
        assert path.variables["bat"] == 7
        assert path.variables["c"] == 7

    def test_function_matches_2(self):
        path = CsvPath()
        path.parse(
            f"""~validation-mode:print,raise~
                    ${NUMBERS}[1*][
                        @x.increase = int(#1)
                        matches() -> push("top", @x)
                    ]"""
        )
        path.fast_forward()
        assert path.variables["top"] == [1, 2, 3, 5, 9]
        assert path.variables["x"] == 9
