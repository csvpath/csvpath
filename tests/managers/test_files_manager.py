import unittest
from csvpath import CsvPaths

DIR = "tests/test_resources/named_files"
JSON = "tests/test_resources/named_files.json"


class TestFilesManager(unittest.TestCase):
    def test_files_mgr_dir1(self):
        print("")
        paths = CsvPaths()
        fm = paths.files_manager
        fm.add_named_files_from_dir(DIR)
        assert fm.named_files
        assert len(fm.named_files) == 4

    def test_files_mgr_json1(self):
        print("")
        paths = CsvPaths()
        fm = paths.files_manager
        fm.set_named_files_from_json(JSON)
        assert fm.named_files
        assert len(fm.named_files) == 2

    def test_files_mgr_dict1(self):
        print("")
        paths = CsvPaths()
        fm = paths.files_manager
        nf = {"wonderful": "a path", "amazing": "another path"}
        fm.set_named_files(nf)
        assert fm.named_files
        assert len(fm.named_files) == 2

    def test_files_mgr_dict2(self):
        print("")
        paths = CsvPaths()
        fm = paths.files_manager
        nf = {"wonderful": "a path", "amazing": "another path"}
        fm.set_named_files(nf)
        assert fm.named_files
        assert len(fm.named_files) == 2
        fm.add_named_file(name="outstanding", path="a third path")
        assert len(fm.named_files) == 3
        afile = fm.get_named_file("wonderful")
        assert afile == "a path"
        fm.remove_named_file("wonderful")
        assert len(fm.named_files) == 2
        assert "wonderful" not in fm.named_files
