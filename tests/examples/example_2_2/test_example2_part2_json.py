import unittest
import os
from csvpath import CsvPaths
from csvpath.util.nos import Nos


class TestJsonNamedPaths(unittest.TestCase):
    def test_named_paths_json_load_only(self):
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
        print("")
        #
        # adding files and paths more than 1x is optional, but a good idea for tests because
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
        result = paths.results_manager.get_specific_named_result("orders", "prices")
        valid = paths.results_manager.is_valid("orders")
        assert not valid

        a = f"{paths.config.archive_path}/orders"
        assert Nos(a).dir_exists()
        dirs = Nos(a).listdir()
        dirs = [
            os.path.join(a, d) for d in dirs if not Nos(os.path.join(a, d)).isfile()
        ]
        file = f"{result.run_dir}/prices/unmatched.csv"
        assert Nos(file).exists()

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
        print(f"test_result_manifest: get_specific_named_result_manifest: m: {m}")
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
