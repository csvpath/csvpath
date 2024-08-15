import unittest
from csvpath import CsvPaths

DIR = "tests/test_resources/named_paths"
JSON = "tests/test_resources/named_paths.json"


class TestPathsManager(unittest.TestCase):

    """
    # this test works fine by itself, but when run with the other
    # ~200 it consistently fails. wtf?
    def test_named_paths_dir1(self):
        print("")
        paths = CsvPaths()
        pm = paths.paths_manager
        pm.add_named_paths_from_dir(dir_path=DIR)
        print(f"test_named_paths_dir1: named paths: {pm.named_paths}")
        assert pm.named_paths
        assert len(pm.named_paths) == 1
        assert "many" in pm.named_paths
        assert len(pm.named_paths["many"]) == 2
    """

    def test_named_paths_json1(self):
        print("")
        paths = CsvPaths()
        pm = paths.paths_manager
        pm.set_named_paths_from_json(file_path=JSON)
        assert pm.named_paths
        assert len(pm.named_paths) == 3
        assert "many" in pm.named_paths
        assert "numbers" in pm.named_paths
        assert "needs split" in pm.named_paths
        assert len(pm.named_paths["numbers"]) == 2
        assert len(pm.named_paths["needs split"]) == 2

    def test_named_paths_dict1(self):
        print("")
        paths = CsvPaths()
        pm = paths.paths_manager
        np = ["wonderful", "amazing"]
        pm.add_named_paths("many", np)
        assert pm.named_paths
        assert len(pm.named_paths) == 1
        assert "many" in pm.named_paths
        assert len(pm.named_paths["many"]) == 2

    def test_named_paths_dict2(self):
        print("")
        paths = CsvPaths()
        pm = paths.paths_manager
        np = ["wonderful", "amazing"]
        pm.add_named_paths("many", np)
        assert pm.named_paths
        assert len(pm.named_paths) == 1
        pm.add_named_paths("numbers", "a third path")
        assert len(pm.named_paths) == 2
        apaths = pm.get_named_paths("many")
        assert len(apaths) == 2
        pm.remove_named_paths("many")
        assert len(pm.named_paths) == 1
        assert "many" not in pm.named_paths
