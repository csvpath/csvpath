import unittest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}header_mismatch.csv"
PATH2 = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}header_reset.csv"


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

    def test_function_reset_headers2(self):
        path = CsvPath()
        path.collect(
            f"""${PATH2}[1*][

               line_number() == 18 -> reset_headers(skip())

               ~ these match the last three rows so we're get three False ~
               @m = header_names_mismatch.u("agency|neighborhood|project|outcome")
               push( "n", @m )
               print("$.csvpath.line_number: m: $.variables.m")

               print("$.csvpath.line_number:
present: $.variables.u_present")
               print("misordered: $.variables.u_misordered")
               print("unmatched: $.variables.u_unmatched")
               print("duplicated: $.variables.u_duplicated")

            ]"""
        )
        assert path.variables["n"].count(False) == 3
