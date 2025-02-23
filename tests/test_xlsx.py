import unittest
import os
from csvpath import CsvPaths

FILES = {
    "energy": f"tests{os.sep}test_resources{os.sep}xlsx{os.sep}2023-reported-energy-and-water-metrics.xlsx",
    "primary": f"tests{os.sep}test_resources{os.sep}xlsx{os.sep}Table_1.1_Primary_Energy_Overview.xlsx",
}
NAMED_PATHS_DIR = f"tests{os.sep}test_resources{os.sep}xlsx{os.sep}named_paths"


class TestXlsx(unittest.TestCase):
    def test_csvpaths_xlsx_primary_1(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.file_manager.set_named_files(FILES)
        paths.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        paths.collect_paths(filename="primary", pathsname="primary")
        pathresults = paths.results_manager.get_named_results("primary")
        results = pathresults[0]
        valid = paths.results_manager.is_valid("primary")
        # set for no-fail
        assert valid
        # increase rejects most of the lines
        assert len(results) == 22

    def test_csvpaths_bytes_written_1(self):
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.file_manager.set_named_files(FILES)
        paths.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        paths.collect_paths(filename="energy", pathsname="bytes")
        assert paths.results_manager.is_valid("bytes")
