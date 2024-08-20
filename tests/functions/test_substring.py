import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsSubstring(unittest.TestCase):
    def test_function_substring(self):
        path = CsvPath()
        Save._save(path, "test_function_substring")
        path.parse(
            f"""
            ${PATH}[*]
            [
                @i = substring("testtest", 4)
            ]"""
        )
        lines = path.collect()
        print(f"test_function_substring: path vars: {path.variables}")
        assert len(lines) == 9
        assert path.variables["i"] == "test"
