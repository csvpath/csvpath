import unittest
import os
from csvpath.csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsConcat(unittest.TestCase):
    def test_function_concat1(self):
        path = CsvPath()
        path.parse(
            f"""
                        ${PATH}[*]
                               [ #0 == concat("B" , "ird") ]
                   """
        )
        lines = path.collect()
        assert len(lines) == 1

    def test_function_concat2(self):
        path = CsvPath()
        path.parse(
            f"""
                        ${PATH}[1]
                               [ @bs = concat("B" , "ird", "s") ]
                   """
        )
        path.collect()
        assert path.variables["bs"] == "Birds"

    def test_function_concat3(self):
        path = CsvPath()
        path.parse(
            f"""
                        ${PATH}[1]
                        [
                            push("bird", "red")
                            push("bird", ",blue")
                            push("bird", ",green")
                            push("bird", ",yellow")
                            @bs = concat("B" , "irds: ", @bird)
                        ]
                   """
        )
        path.collect()
        assert path.variables["bs"] == "Birds: red,blue,green,yellow"
