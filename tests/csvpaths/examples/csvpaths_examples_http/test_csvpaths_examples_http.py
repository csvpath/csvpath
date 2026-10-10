import unittest
from csvpath import CsvPaths


class TestCsvPathsExamplesHttp(unittest.TestCase):
    def test_load_from_http(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.config.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.file_manager.add_named_file(
            name="orders",
            #
            # used food.csv as shared to anyone by link in google drive
            #
            # create download link to google drive:
            #   https://sites.google.com/site/gdocs2direct/?pli=1&authuser=0
            #
            path="https://drive.google.com/uc?export=download&id=1PVB1J3W-fpGwBcc8oMhbwK6CLsHZrBjH",
        )
        paths.file_manager.registrar.patch_named_file(
            name="orders", patch={"type": "csv", "file_name": "download.csv"}
        )
        paths.paths_manager.add_named_paths(name="http", paths=["$[*][yes()]"])

        paths.collect_paths(pathsname="http", filename="orders")
        results = paths.results_manager.get_named_results("http")
        assert len(results) == 1
        assert len(results[0]) > 10
