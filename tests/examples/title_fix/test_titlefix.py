import unittest
import os
from csvpath import CsvPaths


class TestTitleFix(unittest.TestCase):
    def test_title_fix(self):
        paths = CsvPaths()
        paths.config.add_to_config("listeners", "groups", "sftpplus", save_load=False)
        paths.config.add_to_config(
            "listeners",
            "sftpplus.paths",
            "from csvpath.managers.integrations.sftpplus.sftpplus_listener import SftpPlusListener",
            save_load=False,
        )
        paths.file_manager.add_named_file(
            name="title_fix", path="tests/examples/title_fix/assets/checkouts.csv"
        )
        paths.paths_manager.add_named_paths_from_file(
            name="title_fix",
            file_path="tests/examples/title_fix/assets/title_fix.csvpaths",
        )
        paths.collect_paths(filename="title_fix", pathsname="title_fix")
        results = paths.results_manager.get_named_results("title_fix")
        assert len(results) == 1
        result = results[0]
        d = result.data_file_path
        with open(d, "r", encoding="utf-8") as file:
            s = file.read()
            assert s.find("Great circle : a novel / Maggie Shipstead") == -1
