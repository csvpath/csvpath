import unittest
import os
from csvpath.csvpath import CsvPath

PATH = f"tests{os.sep}test_resources{os.sep}count_physical_lines.csv"
EMPTY = f"tests{os.sep}test_resources{os.sep}empty3.csv"


class TestFunctionsAfterBlank(unittest.TestCase):
    def test_function_after_blank1(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*] [
                after_blank() -> push( "after", line_number() )
            ]
            """
        )
        path.collect()
        assert path.variables["after"] == [5, 7]

    def test_function_after_blank2(self):
        path = CsvPath()
        path.parse(
            f""" ${EMPTY}[*] [
                after_blank() -> push( "after", line_number() )
            ]
            """
        )
        path.collect()
        assert "after" in path.variables
        assert path.variables["after"] == [5, 9]
