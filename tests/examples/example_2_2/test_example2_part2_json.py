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
            f"tests{os.sep}examples{os.sep}example_2_2{os.sep}orders.json"
        )

    def test_json_named_file_load_only(self):
        paths = CsvPaths()
        print("")
        #
        # adding files and paths more than 1x is optional, but a good idea for tests because
        # the source test files and dirs could change.
        #
        paths.file_manager.add_named_files_from_dir(
            f"tests{os.sep}examples{os.sep}example_2_2{os.sep}csvs"
        )

    def test_json_named_paths(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        #
        # adding files and paths is optional, but a good idea for tests because
        # the source test files and dirs could change.
        #
        paths.file_manager.add_named_files_from_dir(
            f"tests{os.sep}examples{os.sep}example_2_2{os.sep}csvs"
        )
        paths.paths_manager.add_named_paths_from_json(
            f"tests{os.sep}examples{os.sep}example_2_2{os.sep}orders.json"
        )
        paths.collect_paths(filename="March-2024", pathsname="orders")
        result = paths.results_manager.get_specific_named_result("orders", "prices")
        valid = paths.results_manager.is_valid("orders")
        assert not valid

        a = f"{paths.config.archive_path}{os.sep}orders"
        assert Nos(a).dir_exists()
        dirs = Nos(a).listdir()
        dirs = [
            os.path.join(a, d) for d in dirs if not Nos(os.path.join(a, d)).isfile()
        ]
        file = f"{result.run_dir}{os.sep}prices{os.sep}unmatched.csv"
        assert Nos(file).exists()

    def test_result_manifest(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        #
        # setup
        #
        paths.config.add_to_config("errors", "csvpath", "raise, print")
        paths.file_manager.add_named_files_from_dir(
            f"tests{os.sep}examples{os.sep}example_2_2{os.sep}csvs"
        )
        paths.paths_manager.add_named_paths_from_json(
            f"tests{os.sep}examples{os.sep}example_2_2{os.sep}expected_files.json"
        )
        paths.collect_paths(filename="March-2024", pathsname="expected_files")
        #
        # check categories results
        #
        m = paths.results_manager.get_specific_named_result_manifest(
            "expected_files", "categories_b"
        )
        r = paths.results_manager.get_specific_named_result(
            "expected_files", "categories_b"
        )
        assert r.is_valid
        assert m["files_expected"] is False
        #
        # prices
        #
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
        #
        # sku_upc results
        #
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
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        try:
            os.remove(f"transfers{os.sep}transfer.txt")
        except FileNotFoundError:
            pass

        paths.file_manager.add_named_files_from_dir(
            f"tests{os.sep}examples{os.sep}example_2_2{os.sep}csvs"
        )
        paths.paths_manager.add_named_paths_from_json(
            f"tests{os.sep}examples{os.sep}example_2_2{os.sep}transfer.json"
        )
        paths.collect_paths(filename="March-2024", pathsname="transfer")
        assert os.path.exists(f"transfers{os.sep}transfer.txt")
