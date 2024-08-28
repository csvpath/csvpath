import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsInt(unittest.TestCase):
    def test_function_int1(self):
        path = CsvPath()
        Save._save(path, "test_function_int1")
        path.parse(
            f""" ${PATH}[*] [
                @st = int(" ")
                @no = int(none())
                @bo = int(no())
            ]
            """
        )
        print("")
        lines = path.collect()
        print(f"test_function_int1: path vars: {path.variables}")
        print(f"test_function_int1: lines: {lines}")
        assert path.variables["st"] == 0
        assert path.variables["no"] == 0
        assert path.variables["bo"] == 0
