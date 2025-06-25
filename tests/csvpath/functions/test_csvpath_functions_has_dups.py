import unittest
import os
from csvpath import CsvPath

NUMBERS = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}numbers.csv"
PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsHasDups(unittest.TestCase):
    def test_function_has_dups1(self):
        path = CsvPath()
        path.parse(
            f""" ${NUMBERS}[*] [
                @d = dup_lines()
                dup_lines() -> print("line $.csvpath.line_count has dups in $.variables.d")
                @c = count_dups.two()
            ]
            """
        )
        lines = path.collect()
        assert path.variables["d"] == [4, 5, 6, 7]
        assert len(lines) == 3
        assert path.variables["c"] == 4

    def test_function_has_dups2(self):
        path = CsvPath()
        path.parse(
            f""" ${NUMBERS}[*] [
                @d = dup_lines(#0,#1)
                dup_lines(#0,#1) -> print("line $.csvpath.line_count has dups in $.variables.d ")
                @c = count_dups(#0,#1)
           ]
            """
        )
        lines = path.collect()
        assert path.variables["d"] == [4, 5, 6, 7]
        assert len(lines) == 3
        assert path.variables["c"] == 4

    def test_function_has_dups3(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise, print")
        path.parse(
            f""" ${PATH}[*] [
                @d = dup_lines(#1)
                @c = count_dups.two(#1,#0)
                dup_lines(#1) -> print("line $.csvpath.line_count has dups in $.variables.d")
            ]
            """
        )
        lines = path.collect()
        assert path.variables["d"] == [2, 3, 4, 5, 6, 7, 8]
        assert len(lines) == 6
        assert path.variables["c"] == 2
