import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

NUMBERS = "tests/test_resources/numbers.csv"
PATH = "tests/test_resources/test.csv"


class TestFunctionsHasDups(unittest.TestCase):
    def test_function_has_dups1(self):
        path = CsvPath()
        Save._save(path, "test_function_has_dups1")
        path.parse(
            f""" ${NUMBERS}[*] [
                @d = dup_lines()
                dup_lines() -> print("line $.csvpath.line_count has dups in $.variables.d")
                @c = count_dups.two()
            ]
            """
        )
        print("")
        lines = path.collect()
        print(f"\n test_function_has_dups1: path vars: {path.variables}")
        print(f"\n test_function_has_dups1: lines: {lines}")
        assert path.variables["d"] == [4, 5, 6]
        assert len(lines) == 3
        assert path.variables["c"] == 4

    def test_function_has_dups2(self):
        path = CsvPath()
        Save._save(path, "test_function_has_dups2")
        path.parse(
            f""" ${NUMBERS}[*] [
                @d = dup_lines(#0,#1)
                dup_lines(#0,#1) -> print("line $.csvpath.line_count has dups in $.variables.d")
                @c = count_dups(#0,#1)
           ]
            """
        )
        print("")
        lines = path.collect()
        print(f"test_function_has_dups1: path vars: {path.variables}")
        print(f"test_function_has_dups1: lines: {lines}")
        assert path.variables["d"] == [4, 5, 6]
        assert len(lines) == 3
        assert path.variables["c"] == 4

    def test_function_has_dups3(self):
        path = CsvPath()
        Save._save(path, "test_function_has_dups3")
        path.parse(
            f""" ${PATH}[*] [
                @d = dup_lines(#1)
                @c = count_dups.two(#1,#0)
                dup_lines(#1) -> print("line $.csvpath.line_count has dups in $.variables.d")
            ]
            """
        )
        print("")
        lines = path.collect()
        print(f"test_function_has_dups1: path vars: {path.variables}")
        print(f"test_function_has_dups1: lines: {lines}")
        assert path.variables["d"] == [2, 3, 4, 5, 6, 7]
        assert len(lines) == 6
        assert path.variables["c"] == 2
