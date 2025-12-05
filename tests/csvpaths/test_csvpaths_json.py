import unittest
import os
from csvpath import CsvPaths

JSONL_PATH = os.path.join("tests", "csvpaths", "test_resources", "test.jsonl")
JSONL_CSVPATH = os.path.join(
    "tests", "csvpaths", "test_resources", "named_paths", "jsonl.csvpaths"
)


class TestCsvpathsJsonl(unittest.TestCase):
    def test_csvpaths_jsonl_1(self):
        paths = CsvPaths()
        paths.file_manager.add_named_file(name="jsonl", path=JSONL_PATH)
        paths.paths_manager.add_named_paths_from_file(
            name="jsonl", file_path=JSONL_CSVPATH
        )
        ref = paths.collect_paths(filename="jsonl", pathsname="jsonl")
        assert ref is not None
        results = paths.results_manager.get_named_results("jsonl")
        assert len(results) == 1
        assert results[0].has_errors() is False
        print(f"result vars: {results[0].csvpath.variables}")
