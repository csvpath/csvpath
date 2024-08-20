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
                @d = has_dups()
                not(empty(@d)) -> print("line $.line_count has dups in $.variables.d")

            ]
            """
        )
        print("")
        lines = path.collect()
        print(f"test_function_has_dups1: path vars: {path.variables}")
        print(f"test_function_has_dups1: lines: {lines}")
        assert path.variables["d"] == [4, 5, 6, 7]
        assert len(lines) == 3

    def test_function_has_dups2(self):
        path = CsvPath()
        Save._save(path, "test_function_has_dups2")
        path.parse(
            f""" ${NUMBERS}[*] [
                @d = has_dups(#0,#1)
                not(empty(@d)) -> print("line $.line_count has dups in $.variables.d")

            ]
            """
        )
        print("")
        lines = path.collect()
        print(f"test_function_has_dups1: path vars: {path.variables}")
        print(f"test_function_has_dups1: lines: {lines}")
        assert path.variables["d"] == [4, 5, 6, 7]
        assert len(lines) == 3

    def test_function_has_dups3(self):
        path = CsvPath()
        Save._save(path, "test_function_has_dups3")
        path.parse(
            f""" ${PATH}[*] [
                @d = has_dups(#1)
                not(empty(@d)) -> print("line $.line_count has dups in $.variables.d")

            ]
            """
        )
        print("")
        lines = path.collect()
        print(f"test_function_has_dups1: path vars: {path.variables}")
        print(f"test_function_has_dups1: lines: {lines}")
        assert path.variables["d"] == [2, 3, 4, 5, 6, 7, 8]
        assert len(lines) == 6
