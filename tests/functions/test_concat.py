import unittest
from csvpath.csvpath import CsvPath

PATH = "tests/test_resources/test.csv"


class TestFunctionsConcat(unittest.TestCase):
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
