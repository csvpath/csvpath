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
        print(f"test_function_concat: lines: {len(lines)}")
        assert len(lines) == 1

    def test_function_concat2(self):
        path = CsvPath()
        path.parse(
            f"""
                        ${PATH}[1]
                               [ @bs = concat("B" , "ird", "s") ]
                   """
        )
        path.fast_forward()
        print(f"test_function_concat: variables: {path.variables}")
        assert path.variables["bs"] == "Birds"
