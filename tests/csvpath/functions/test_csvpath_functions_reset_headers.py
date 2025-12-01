import unittest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}header_mismatch.csv"
PATH2 = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}header_reset.csv"
PATH3 = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsResetHeaders(unittest.TestCase):
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

    def test_function_reset_headers3(self):
        path = CsvPath()
        path.collect(
            f"""${PATH3}[*][
                odd(line_number()) -> reset_headers.odd_lines()
            ]"""
        )
        assert "odd_lines_count" in path.variables
        assert path.variables["odd_lines_count"] == 4

        assert "odd_lines_lines" in path.variables
        assert path.variables["odd_lines_lines"] == [1, 3, 5, 7]
