import unittest
import os
from csvpath import CsvPath

PATH = "tests/test_resources/header_mismatch.csv"


class TestFunctionsResetHeaders(unittest.TestCase):
    def test_function_reset_headers1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*][
                gt(count_headers_in_line(),  count_headers()) -> reset_headers()
                @number_of_headers = count_headers()
                push("last_header", end())

            ]"""
        )
        path.collect()
        assert path.variables["number_of_headers"] == 13
