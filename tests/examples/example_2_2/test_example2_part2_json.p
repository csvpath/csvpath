import unittest
from csvpath import CsvPaths


class TestJsonNamedPaths(unittest.TestCase):
    def test_json_named_paths(self):
        paths = CsvPaths()
        paths.file_manager.add_named_files_from_dir("tests/examples/example_2_2/csvs")
        paths.paths_manager.add_named_paths_from_json(
            "tests/examples/example_2_2/orders.json"
        )

        paths.collect_paths(filename="March-2024", pathsname="orders")

        valid = paths.results_manager.is_valid("orders")
        print(f"is valid: {valid}")
