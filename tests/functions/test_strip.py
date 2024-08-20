import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save


PATH = "tests/test_resources/test.csv"


class TestFunctionsStrip(unittest.TestCase):
    def test_function_strip(self):
        path = CsvPath()
        Save._save(path, "test_function_strip")
        path.parse(
            f"""
            ${PATH}[1]
            [
                @trimmable = "  test  "
                @trimmed = strip(@trimmable)
            ]"""
        )
        path.fast_forward()
        print(f"test_function_strip: path vars: {path.variables}")
        assert path.variables["trimmable"] == "  test  "
        assert path.variables["trimmed"] == "test"
