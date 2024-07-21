import unittest
from csvpath.csvpaths import CsvPaths

PATH = "tests/test_resources/test.csv"
NUMBERS = "tests/test_resources/numbers.csv"
JSON = "tests/test_resources/named_files.json"
DIR = "tests/test_resources"
DIR2 = "tests/test_resources/"


class TestCsvPaths(unittest.TestCase):
    def test_dict(self):
        print("")
        d = {"test": PATH, "numbers": NUMBERS}
        paths = CsvPaths(named_files=d)
        path = paths.csvpath()
        filepath = "$test[*][yes()]"
        filepath2 = path._update_file_path(filepath)
        print(f"\ntest_dict: path: {filepath} ~= {filepath2}")
        assert filepath2 is not None
        assert filepath2 == f"${PATH}[*][yes()]"

    def test_json(self):
        print("")
        paths = CsvPaths(filename=JSON)
        path = paths.csvpath()
        filepath = "$test[*][yes()]"
        filepath2 = path._update_file_path(filepath)
        print(f"\ntest_dict: path: {filepath} ~= {filepath2}")
        assert filepath2 is not None
        assert filepath2 == f"${PATH}[*][yes()]"

    def test_file(self):
        print("")
        paths = CsvPaths(filename=PATH)
        path = paths.csvpath()
        filepath = "$test[*][yes()]"
        filepath2 = path._update_file_path(filepath)
        print(f"\ntest_dict: path: {filepath} ~= {filepath2}")
        assert filepath2 is not None
        assert filepath2 == f"${PATH}[*][yes()]"

    def test_dir1(self):
        print("")
        paths = CsvPaths(filename=DIR)
        path = paths.csvpath()
        filepath = "$test[*][yes()]"
        filepath2 = path._update_file_path(filepath)
        print(f"\ntest_dict: path: filepath: {filepath} ~= filepath2: {filepath2}")
        expected = f"${PATH}[*][yes()]"
        print(f"\ntest_dict: path: filepath2: {filepath2} ~= expected: {expected}")
        assert filepath2 is not None
        assert filepath2 == expected

    def test_dir2(self):
        print("")
        paths = CsvPaths(filename=DIR2)
        path = paths.csvpath()
        filepath = "$test[*][yes()]"
        filepath2 = path._update_file_path(filepath)
        print(f"\ntest_dict: path: {filepath} ~= {filepath2}")
        assert filepath2 is not None
        assert filepath2 == f"${PATH}[*][yes()]"

    def test_no_named_file_match(self):
        print("")
        paths = CsvPaths()
        path = paths.csvpath()
        filepath = f"${PATH}[*][yes()]"
        filepath2 = path._update_file_path(filepath)
        print(f"\ntest_dict: path: {filepath} ~= {filepath2}")
        assert filepath2 is not None
        assert filepath2 == filepath
