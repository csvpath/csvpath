import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/count_physical_lines.csv"
EMPTY = "tests/test_resources/empty3.csv"


class TestFunctionsAfterBlank(unittest.TestCase):
    def test_function_after_blank1(self):
        path = CsvPath()
        Save._save(path, "test_function_after_blank1")
        path.parse(
            f""" ${PATH}[*] [
                after_blank() -> push( "after", line_number() )
            ]
            """
        )
        print("")
        lines = path.collect()
        print(f"test_function_after_blank1: path vars: {path.variables}")
        print(f"test_function_after_blank1: lines: {lines}")
        assert path.variables["after"] == [5, 7]

    def test_function_after_blank2(self):
        path = CsvPath()
        Save._save(path, "test_function_after_blank2")
        path.parse(
            f""" ${EMPTY}[*] [
                after_blank() -> push( "after", line_number() )
            ]
            """
        )
        print("")
        lines = path.collect()
        print(f"test_function_after_blank2: path vars: {path.variables}")
        print(f"test_function_after_blank2: lines: {lines}")
        assert "after" in path.variables
        assert path.variables["after"] == [5, 9]
