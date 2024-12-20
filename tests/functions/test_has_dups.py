import unittest
from csvpath import CsvPath

NUMBERS = "tests/test_resources/numbers.csv"
PATH = "tests/test_resources/test.csv"


class TestFunctionsHasDups(unittest.TestCase):
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
        assert path.variables["d"] == [4, 5, 6]
        assert len(lines) == 3
        assert path.variables["c"] == 4

    def test_function_has_dups2(self):
        path = CsvPath()
        path.parse(
            f""" ${NUMBERS}[*] [
                @d = dup_lines(#0,#1)
                dup_lines(#0,#1) -> print("line $.csvpath.line_count has dups in $.variables.d")
                @c = count_dups(#0,#1)
           ]
            """
        )
        lines = path.collect()
        assert path.variables["d"] == [4, 5, 6]
        assert len(lines) == 3
        assert path.variables["c"] == 4

    def test_function_has_dups3(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*] [
                @d = dup_lines(#1)
                @c = count_dups.two(#1,#0)
                dup_lines(#1) -> print("line $.csvpath.line_count has dups in $.variables.d")
            ]
            """
        )
        lines = path.collect()
        assert path.variables["d"] == [2, 3, 4, 5, 6, 7]
        assert len(lines) == 6
        assert path.variables["c"] == 2
