import unittest
from csvpath import CsvPaths
from csvpath.managers.csvpaths_manager import PathsManager

DIR = "tests/test_resources/named_paths"
JSON = "tests/test_resources/named_paths.json"


class TestPathsManager(unittest.TestCase):
    def test_named_paths_json1(self):
        print("")
        paths = CsvPaths()
        pm = paths.paths_manager
        pm.add_named_paths_from_json(file_path=JSON)
        assert pm.named_paths
        assert len(pm.named_paths) == 3
        assert "many" in pm.named_paths
        assert "numbers" in pm.named_paths
        assert "needs split" in pm.named_paths
        assert len(pm.named_paths["numbers"]) == 3
        assert len(pm.named_paths["needs split"]) == 1

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
        pm.add_named_paths("numbers", ["a third path"])
        assert len(pm.named_paths) == 2
        apaths = pm.get_named_paths("many")
        assert len(apaths) == 2
        pm.remove_named_paths("many")
        assert len(pm.named_paths) == 1
        assert "many" not in pm.named_paths

    # need:
    # . all in directory under one name
    # . add duplicates to name
    def test_named_paths_dir(self):
        print("")
        paths = CsvPaths()
        pm = paths.paths_manager
        pm.add_named_paths_from_dir(directory=DIR)
        assert pm.named_paths
        assert len(pm.named_paths) == 10

        paths2 = CsvPaths()
        pm2 = paths2.paths_manager
        pm2.add_named_paths_from_dir(directory=DIR, name="many")
        assert paths2.paths_manager.named_paths
        for k, v in paths2.paths_manager.named_paths.items():
            print(f"test_named_paths_dir: k: {k} = {len(v)}")
        assert len(pm2.named_paths) == 1
