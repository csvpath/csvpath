import unittest
import os
from csvpath import CsvPaths
from csvpath.util.nos import Nos

JSON = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_example_2_2{os.sep}orders.json"
EJSON = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_example_2_2{os.sep}expected_files.json"
CSVS = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_example_2_2{os.sep}csvs"
TJSON = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_example_2_2{os.sep}transfer.json"


class TestCsvPathsExamplesJsonNamedPaths(unittest.TestCase):
    def test_named_paths_json_load_only(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpaths", "raise, collect, print")
        #
        # adding files and paths is optional, but a good idea for tests because
        # the source test files and dirs could change.
        #
        paths.paths_manager.add_named_paths_from_json(JSON)

    def test_json_named_file_load_only(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpaths", "raise, collect, print")
        #
        # adding files and paths more than 1x is optional, but a good idea for tests because
        # the source test files and dirs could change.
        #
        paths.file_manager.add_named_files_from_dir(CSVS)

    def test_json_named_paths(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        #
        # adding files and paths is optional, but a good idea for tests because
        # the source test files and dirs could change.
        #
        import time

        # t1 = time.perf_counter()
        paths.file_manager.add_named_files_from_dir(CSVS)
        # t2 = time.perf_counter()
        # print(f"1: {t2-t1}")

        paths.paths_manager.add_named_paths_from_json(JSON)
        # t3 = time.perf_counter()
        # print(f"2: {t3-t2}")

        paths.collect_paths(filename="March-2024", pathsname="orders")
        # t4 = time.perf_counter()
        # print(f"3: {t4-t3}")

        #
        #
        #
        result = paths.results_manager.get_specific_named_result("orders", "prices")
        valid = paths.results_manager.is_valid("orders")
        assert not valid
        # t5 = time.perf_counter()
        # print(f"4: {t5-t4}")

        a = f"{paths.config.archive_path}{os.sep}orders"
        assert Nos(a).dir_exists()
        dirs = Nos(a).listdir()
        dirs = [
            os.path.join(a, d) for d in dirs if not Nos(os.path.join(a, d)).isfile()
        ]
        file = f"{result.run_dir}{os.sep}prices{os.sep}unmatched.csv"
        assert Nos(file).exists()
        # t6 = time.perf_counter()
        # print(f"5: {t6-t5}")

    def test_result_manifest(self):
        paths = CsvPaths()
        #
        # setup
        #
        paths.config.add_to_config("errors", "csvpaths", "raise, print")
        paths.config.add_to_config("errors", "csvpath", "raise, print")

        # tests/csvpaths/examples/csvpaths_examples_example_2_2/csvs

        paths.file_manager.add_named_files_from_dir(
            f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_example_2_2{os.sep}csvs"
        )
        assert paths.file_manager.get_named_file("March-2024") is not None
        paths.paths_manager.add_named_paths_from_json(EJSON)
        paths.collect_paths(filename="March-2024", pathsname="expected_files")
        #
        # check categories results
        #
        resman = paths.results_manager
        m = resman.get_specific_named_result_manifest("expected_files", "categories_b")
        r = resman.get_specific_named_result("expected_files", "categories_b")
        assert r.is_valid
        assert m["files_expected"] is False
        #
        # prices
        #
        m = resman.get_specific_named_result_manifest("expected_files", "prices_b")
        r = resman.get_specific_named_result("expected_files", "prices_b")
        assert r.is_valid is False
        assert m["files_expected"] is True
        assert "file_fingerprints" in m
        assert len(m["file_fingerprints"]) == 6
        #
        # sku_upc results
        #
        m = resman.get_specific_named_result_manifest("expected_files", "sku_upc_b")
        r = resman.get_specific_named_result("expected_files", "sku_upc_b")
        assert "completed" in m
        assert m["completed"] is False

    def test_transfer_mode(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        try:
            os.remove(f"transfers{os.sep}transfer.txt")
        except FileNotFoundError:
            pass
        paths.file_manager.add_named_files_from_dir(CSVS)
        paths.paths_manager.add_named_paths_from_json(TJSON)
        paths.collect_paths(filename="March-2024", pathsname="transfer")
        assert os.path.exists(f"transfers{os.sep}transfer.txt")
