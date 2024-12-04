import unittest
import os
from csvpath import CsvPaths


class TestJsonNamedPaths(unittest.TestCase):
    def test_json_named_paths_load_only(self):
        paths = CsvPaths()
        #
        # adding files and paths is optional, but a good idea for tests because
        # the source test files and dirs could change.
        #
        paths.paths_manager.add_named_paths_from_json(
            "tests/examples/example_2_2/orders.json"
        )

    def test_json_named_file_load_only(self):
        paths = CsvPaths()
        #
        # adding files and paths is optional, but a good idea for tests because
        # the source test files and dirs could change.
        #
        paths.file_manager.add_named_files_from_dir("tests/examples/example_2_2/csvs")

    def test_json_named_paths(self):
        paths = CsvPaths()
        #
        # adding files and paths is optional, but a good idea for tests because
        # the source test files and dirs could change.
        #
        paths.file_manager.add_named_files_from_dir("tests/examples/example_2_2/csvs")
        paths.paths_manager.add_named_paths_from_json(
            "tests/examples/example_2_2/orders.json"
        )
        paths.collect_paths(filename="March-2024", pathsname="orders")
        paths.results_manager.get_specific_named_result("orders", "prices")
        valid = paths.results_manager.is_valid("orders")
        assert not valid

        a = "archive/orders"
        dirs = os.listdir(a)
        dirs = [os.path.join(a, d) for d in dirs if os.path.isdir(os.path.join(a, d))]
        n = max(dirs, key=os.path.getmtime)
        file = f"{n}/prices/unmatched.csv"
        assert os.path.exists(file)

    def test_result_manifest(self):
        paths = CsvPaths()
        paths.file_manager.add_named_files_from_dir("tests/examples/example_2_2/csvs")
        paths.paths_manager.add_named_paths_from_json(
            "tests/examples/example_2_2/expected_files.json"
        )
        paths.collect_paths(filename="March-2024", pathsname="expected_files")
        m = paths.results_manager.get_specific_named_result_manifest(
            "expected_files", "categories_b"
        )
        r = paths.results_manager.get_specific_named_result(
            "expected_files", "categories_b"
        )
        assert r.is_valid
        assert m["files_expected"] is False
        m = paths.results_manager.get_specific_named_result_manifest(
            "expected_files", "prices_b"
        )
        r = paths.results_manager.get_specific_named_result(
            "expected_files", "prices_b"
        )
        assert r.is_valid is False
        assert m["files_expected"] is True
        assert "file_fingerprints" in m
        assert len(m["file_fingerprints"]) == 6

        m = paths.results_manager.get_specific_named_result_manifest(
            "expected_files", "sku_upc_b"
        )
        r = paths.results_manager.get_specific_named_result(
            "expected_files", "sku_upc_b"
        )
        assert "completed" in m
        assert m["completed"] is False

    def test_transfer_mode(self):
        paths = CsvPaths()
        try:
            os.remove("transfers/transfer.txt")
        except FileNotFoundError:
            pass

        paths.file_manager.add_named_files_from_dir("tests/examples/example_2_2/csvs")
        paths.paths_manager.add_named_paths_from_json(
            "tests/examples/example_2_2/transfer.json"
        )
        paths.collect_paths(filename="March-2024", pathsname="transfer")
        assert os.path.exists("transfers/transfer.txt")
