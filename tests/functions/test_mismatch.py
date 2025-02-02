import unittest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}test_resources{os.sep}header_mismatch.csv"


class TestFunctionsMismatch(unittest.TestCase):
    def test_function_mismatch1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*][
                push( "problems", mismatch())
            ]"""
        )
        path.fast_forward()
        print(f"vars: {path.variables}")
        assert "problems" in path.variables
        assert path.variables["problems"] == [0, 5, 1, 10]

    def test_function_mismatch2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*][
                push( "problems", mismatch("false"))
                push( "signed", mismatch("signed"))
                reset_headers()
            ]"""
        )
        path.fast_forward()
        assert "problems" in path.variables
        assert path.variables["problems"] == [0, 5, -6, 11]
        assert path.variables["problems"] == path.variables["signed"]
