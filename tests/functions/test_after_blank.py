import unittest
from csvpath.csvpath import CsvPath

PATH = "tests/test_resources/count_physical_lines.csv"
EMPTY = "tests/test_resources/empty3.csv"


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
