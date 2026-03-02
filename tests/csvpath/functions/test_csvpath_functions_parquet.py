import unittest
import os
from csvpath.csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsParquet(unittest.TestCase):
    def test_function_parquet_1(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise~
            ${PATH}[*]
            [
                parquet.person(
                    string.firstname(#0),
                    string.lastname(#1),
                    string.say(#2)
                )
            ]"""
        )
        path.fast_forward()
