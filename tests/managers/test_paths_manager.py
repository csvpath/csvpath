import unittest
from csvpath import CsvPaths

DIR = "tests/test_resources/named_paths"
JSON = "tests/test_resources/named_paths.json"


class TestPathsManager(unittest.TestCase):

    """
    def test_multiple_paths_with_metadata(self):
        print("")
        paths = CsvPaths()
        pm = paths.paths_manager
        contents = "" "
        ---- CSVPATH: This is test path #1 ----
        $[*][ yes() ]

        ---- CSVPATH: This is test path #2 ----
        $[*][ no() ]

        ---- CSVPATH: This is test path #3 ----
        $[*][ stop() ]

        ---- CSVPATH ----

        ~ meta-name: This is test path #2
          meta-description: It does stuff
        ~
        $[*][ fail() ]

        "" "
        rs = pm._extract_paths(contents)
        print(f"test_multiple_paths_with_metadata: results: {rs}")
        assert len(rs) == 4
        assert len(rs[0]) == 2
        assert "This is test path #1" == rs[0][1]
        assert "This is test path #3" == rs[2][1]
        assert rs[2][0] == "$[*][ stop() ]"
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
