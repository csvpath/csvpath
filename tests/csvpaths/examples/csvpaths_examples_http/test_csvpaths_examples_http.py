import unittest
import os
from csvpath import CsvPaths


class TestCsvPathsExamplesHttp(unittest.TestCase):
    def test_load_from_http(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.file_manager.add_named_file(
            name="orders",
            path="https://drive.google.com/uc?id=1zO8ekHWx9U7mrbx_0Hoxxu6od7uxJqWw&export=download",
        )
        paths.file_manager.registrar.patch_named_file(
            name="orders", patch={"type": "csv", "file_name": "download.csv"}
        )
        paths.paths_manager.add_named_paths(name="http", paths=["$[*][yes()]"])

        paths.collect_paths(pathsname="http", filename="orders")
        results = paths.results_manager.get_named_results("http")
        assert len(results) == 1
        assert len(results[0]) > 10
