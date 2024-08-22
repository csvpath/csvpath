import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/header_mismatch.csv"


class TestFunctionsResetHeaders(unittest.TestCase):
    def test_function_reset_headers1(self):
        path = CsvPath()
        Save._save(path, "test_function_reset_headers1")
        path.parse(
            f"""
            ${PATH}[*]
            [
                gt(count_headers_in_line(),  count_headers()) -> reset_headers()
                @number_of_headers = count_headers()
                push("last_header", end())

            ]"""
        )
        path.collect()
        print(f"test_function_reset_headers1: path vars: {path.variables}")
        assert path.variables["number_of_headers"] == 13
