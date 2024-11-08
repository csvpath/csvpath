import unittest
import os
from csvpath import CsvPaths


class TestJsonNamedPaths(unittest.TestCase):
    def test_json_named_paths(self):
        paths = CsvPaths()
        paths.file_manager.add_named_files_from_dir("tests/examples/example_2_2/csvs")
        paths.paths_manager.add_named_paths_from_json(
            "tests/examples/example_2_2/orders.json"
        )
        paths.collect_paths(filename="March-2024", pathsname="orders")
        result = paths.results_manager.get_specific_named_result("orders", "prices")
        print(f"result: {result}")
        valid = paths.results_manager.is_valid("orders")
        print(f"is valid: {valid}")
        assert not valid

        a = "archive/orders"
        dirs = os.listdir(a)
        dirs = [os.path.join(a, d) for d in dirs if os.path.isdir(os.path.join(a, d))]
        n = max(dirs, key=os.path.getmtime)
        file = f"{n}/prices/unmatched.csv"
        print(f"file: {file}")
        assert os.path.exists(file)
