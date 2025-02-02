import unittest
import os
from csvpath import CsvPaths


class TestCache(unittest.TestCase):
    def test_autogen5_example_run(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.paths_manager.add_named_paths_from_file(
            name="autogen5",
            file_path=f"tests{os.sep}examples{os.sep}autogen5{os.sep}assets{os.sep}accountants.csvpath",
        )
        paths.file_manager.add_named_file(
            name="accounts",
            path=f"tests{os.sep}examples{os.sep}autogen5{os.sep}assets{os.sep}Washington_State_Certified_Public_Accountants.csv",
        )
        paths.fast_forward_paths(pathsname="autogen5", filename="accounts")

    def test_autogen5_paths_load_only(self):
        paths = CsvPaths()
        paths.paths_manager.add_named_paths_from_file(
            name="autogen5",
            file_path=f"tests{os.sep}examples{os.sep}autogen5{os.sep}assets{os.sep}accountants.csvpath",
        )

    def test_autogen5_paths_by_json(self):
        paths = CsvPaths()
        paths.paths_manager.add_named_paths_from_json(
            f"tests{os.sep}examples{os.sep}autogen5{os.sep}two.json"
        )

    def test_autogen5_file_load_only(self):
        paths = CsvPaths()
        paths.file_manager.add_named_file(
            name="accounts",
            path=f"tests{os.sep}examples{os.sep}autogen5{os.sep}assets{os.sep}Washington_State_Certified_Public_Accountants.csv",
        )
