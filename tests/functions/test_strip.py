import unittest
from csvpath.csvpath import CsvPath


PATH = "tests/test_resources/test.csv"


class TestFunctionsStrip(unittest.TestCase):
    def test_function_strip(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [
                @t = "  test  "
                @trimmable = @t
                @trimmed = strip(@trimmable)
            ]"""
        )
        path.fast_forward()
        assert path.variables["trimmable"] == "  test  "
        assert path.variables["trimmed"] == "test"
