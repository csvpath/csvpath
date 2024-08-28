import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsConcat(unittest.TestCase):
    def test_function_concat1(self):
        path = CsvPath()
        Save._save(path, "test_function_concat1")
        path.parse(
            f"""
                        ${PATH}[*]
                               [ #0 == concat("B" , "ird") ]
                   """
        )
        lines = path.collect()
        print(f"test_function_concat1: lines: {len(lines)}")
        assert len(lines) == 1

    def test_function_concat2(self):
        path = CsvPath()
        Save._save(path, "test_function_concat2")
        path.parse(
            f"""
                        ${PATH}[1]
                               [ @bs = concat("B" , "ird", "s") ]
                   """
        )
        path.collect()
        print(f"test_function_concat2: variables: {path.variables}")
        assert path.variables["bs"] == "Birds"
