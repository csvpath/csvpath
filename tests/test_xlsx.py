import unittest
from csvpath import CsvPaths

FILES = {
    "energy": "tests/test_resources/xlsx/2023-reported-energy-and-water-metrics.xlsx",
    "primary": "tests/test_resources/xlsx/Table_1.1_Primary_Energy_Overview.xlsx",
}
NAMED_PATHS_DIR = "tests/test_resources/xlsx/named_paths"


class TestXlsx(unittest.TestCase):
    def test_csvpaths_xlsx_primary_1(self):
        paths = CsvPaths()
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
        paths.file_manager.set_named_files(FILES)
        paths.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        paths.collect_paths(filename="energy", pathsname="bytes")
        assert paths.results_manager.is_valid("bytes")
