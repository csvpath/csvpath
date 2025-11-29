import unittest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}numbers.csv"


class TestCsvPathFunctionsFormat(unittest.TestCase):
    def test_function_format_1(self):
        path = CsvPath()
        path.collect(
            f"""
                ${PATH}[2][
                    @f1 = format( float(#0), ".3f" )
                    @f2 = format( int(#0), "0<4" )
                    @f3 = interpolate( int(#0), "Result: {{:.2f}}" )
                ]
            """
        )
        assert path.variables["f1"] == "2.000"
        assert path.variables["f2"] == "2000"
        assert path.variables["f3"] == "Result: 2.00"

    def test_function_format_2(self):
        path = CsvPath()
        path.collect(
            f"""
                ${PATH}[2][
                    @f1 = format( none(), ".3f" )
                ]
            """
        )
        assert path.variables["f1"] is None
