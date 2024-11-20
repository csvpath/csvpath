import unittest
from csvpath.csvpaths import CsvPaths

FILES = {
    "energy": "tests/test_resources/xlsx/2023-reported-energy-and-water-metrics.xlsx",
    "primary": "tests/test_resources/xlsx/Table_1.1_Primary_Energy_Overview.xlsx",
}
NAMED_PATHS_DIR = "tests/test_resources/xlsx/named_paths"


class TestXlsx(unittest.TestCase):
    def test_csvpaths_xlsx_primary_1(self):
        print("")
        cs = CsvPaths()
        cs.file_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.collect_paths(filename="primary", pathsname="primary")

        pathresults = cs.results_manager.get_named_results("primary")
        print(f"pathresults are: {len(pathresults)}")
        results = pathresults[0]
        print(f"results are: {len(results)}")
        valid = cs.results_manager.is_valid("primary")
        # set for no-fail
        assert valid
        # increase rejects most of the lines
        assert len(results) == 22

    def test_csvpaths_bytes_written_1(self):
        print("")
        cs = CsvPaths()
        cs.file_manager.set_named_files(FILES)
        cs.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        cs.collect_paths(filename="energy", pathsname="bytes")
        assert cs.results_manager.is_valid("bytes")
