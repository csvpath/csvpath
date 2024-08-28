import unittest
from csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/header_mismatch.csv"


class TestFunctionsMismatch(unittest.TestCase):
    def test_function_mismatch1(self):
        path = CsvPath()
        Save._save(path, "test_function_mismatch1")
        path.parse(
            f"""
            ${PATH}[*]
            [
                push( "problems", mismatch())
            ]"""
        )
        path.fast_forward()
        print(f"test_function_any_function: path vars: {path.variables}")
        assert "problems" in path.variables
        assert path.variables["problems"] == [0, 5, 1, 0, 10]
