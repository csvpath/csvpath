import unittest
import os
from csvpath.csvpath import CsvPath

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"
PATH2 = f"tests{os.sep}examples{os.sep}max_increase{os.sep}Automobiles_Annual_Imports_and_Exports_Port_Authority_of_NY.csv"
FOOD = f"tests{os.sep}test_resources{os.sep}food.csv"


class TestFunctionsPercentUnique(unittest.TestCase):
    def test_function_percent_unique_1(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[1-4][
                    not(#2 == "ribbit...")
                    @p = percent_unique.last.onmatch( #lastname)
                    print("$.csvpath.line_number: $.headers.lastname")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 3
        assert path.variables["p"] == 50

    def test_function_percent_unique_2(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[1-4][
                    not(#2 == "ribbit...")
                    @p = percent_unique.last( #lastname)
                    print("$.csvpath.line_number: $.headers.lastname")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 3
        assert path.variables["p"] == 50

    def test_function_percent_unique_3(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[1*][
                    not(#2 == "ribbit...")
                    @p = percent_unique.last( #lastname)
                    print("$.csvpath.line_number: $.headers.lastname")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 7
        assert path.variables["p"] == 50

    def test_function_percent_unique_4(self):
        path = CsvPath()
        path.parse(
            f"""${PATH2}[1*][
                 @uniques = percent_unique.onmatch.pu(#"Automobile Volume")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 32
        assert path.variables["pu"]
        assert path.variables["uniques"]
        assert path.variables["uniques"] == 100

    def test_function_percent_unique_5(self):
        path = CsvPath()
        path.parse(
            f"""${FOOD}[1*][
                    @p = percent_unique.last(#1)
                    print("$.csvpath.line_number: $.headers.1")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 10
        assert path.variables["p"] == 40

    def test_function_percent_unique_6(self):
        path = CsvPath()
        path.parse(
            f"""${FOOD}[1*][
                    @p = percent_unique.onmatch.last(#1)
                    not(#1 == "grain")
                    print("$.csvpath.line_number $.headers.1")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 8
        assert path.variables["p"] == 50
