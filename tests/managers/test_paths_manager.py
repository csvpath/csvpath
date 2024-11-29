import unittest
import os
from csvpath import CsvPaths
from csvpath.managers.paths.paths_manager import PathsManager

DIR = "tests/test_resources/named_paths"
JSON = "tests/test_resources/named_paths.json"


class TestPathsManager(unittest.TestCase):
    def test_named_paths_set_named_paths1(self):
        paths = CsvPaths()
        paths.file_manager.add_named_file(
            name="test", path="tests/test_resources/test.csv"
        )
        settings = {}
        settings["settings"] = [
            """$[1][ yes() print("Hi $.csvpath.line_number")]""",
            """$[2][ yes() print("Hi $.csvpath.line_number")]""",
            """$[3][ yes() print("Hi $.csvpath.line_number")]""",
            """$[4][ yes() no() print("Hi $.csvpath.line_number")]""",
        ]
        paths.paths_manager.set_named_paths(settings)
        paths.collect_paths(filename="test", pathsname="settings")
        results = paths.results_manager.get_named_results("settings")
        assert len(results) == 4
        assert len(results[0]) == 1
        assert len(results[1]) == 1
        assert len(results[2]) == 1
        assert len(results[3]) == 0

    def test_named_paths_json1(self):
        paths = CsvPaths()
        pm = paths.paths_manager
        pm.remove_all_named_paths()
        pm.add_named_paths_from_json(file_path=JSON)
        assert pm.has_named_paths("many")
        assert pm.has_named_paths("numbers")
        assert pm.has_named_paths("needs split")
        assert pm.number_of_named_paths("numbers") == 3
        assert pm.number_of_named_paths("needs split") == 1

    def test_named_paths_dict1(self):
        paths = CsvPaths()
        pm = paths.paths_manager
        np = ["~name:wonderful~$[*][yes()]", "~id:amazing~$[*][yes()]"]
        i = pm.total_named_paths()
        if i > 0:
            pm.remove_named_paths("many")
            j = pm.total_named_paths()
            assert j == i - 1
        i = pm.total_named_paths()
        pm.add_named_paths(name="many", paths=np)
        assert pm.total_named_paths() == i + 1
        assert pm.has_named_paths("many")
        assert pm.number_of_named_paths("many") == 2

    def test_named_paths_dict2(self):
        paths = CsvPaths()
        pm = paths.paths_manager
        np = ["~name:wonderful~$[*][yes()]", "~id:amazing~$[*][yes()]"]
        pm.remove_named_paths("numbers")
        pm.remove_named_paths("many")
        i = pm.total_named_paths()
        pm.add_named_paths(name="many", paths=np)
        assert pm.total_named_paths() == i + 1
        pm.add_named_paths(name="numbers", paths=["~id:my 34d~$[*][~a third path~]"])
        assert pm.total_named_paths() == i + 2
        pm.remove_named_paths("many")
        assert pm.total_named_paths() == i + 1

    def test_named_paths_from_and_to_1(self):
        paths = CsvPaths()
        pm = paths.paths_manager
        np = [
            "~id:wonderful~ $[*][#1 yes()]",
            "~Id:amazing~ $[*][#2 yes()]",
            "~name:fun~ $[*][#3 yes()]",
            "~Name:interesting~ $[*][#4 yes()]",
        ]
        pm.add_named_paths(name="many", paths=np)

        paths = pm.get_named_paths("$many.csvpaths.amazing")
        assert len(paths) == 1
        assert paths[0].find("#2") > -1

        paths = pm.get_named_paths("$many.csvpaths.amazing:to")
        assert len(paths) == 2
        assert paths[0].find("#1") > -1
        assert paths[1].find("#2") > -1

        paths = pm.get_named_paths("$many.csvpaths.fun:to")
        assert len(paths) == 3
        assert paths[0].find("#1") > -1
        assert paths[1].find("#2") > -1
        assert paths[2].find("#3") > -1

        paths = pm.get_named_paths("$many.csvpaths.amazing:from")
        assert len(paths) == 3
        assert paths[0].find("#2") > -1
        assert paths[1].find("#3") > -1
        assert paths[2].find("#4") > -1

        paths = pm.get_named_paths("$many.csvpaths.fun:from")
        assert len(paths) == 2
        assert paths[0].find("#3") > -1
        assert paths[1].find("#4") > -1

    # need:
    # . all in directory under one name
    # . add duplicates to name
    def test_named_paths_dir(self):
        paths = CsvPaths()
        pm = paths.paths_manager
        pm.remove_all_named_paths()
        assert pm.total_named_paths() == 0
        pm.add_named_paths_from_dir(directory=DIR)
        files = os.listdir(DIR)
        files = [f for f in files if f.find("csvpath") > -1]
        assert pm.total_named_paths() == len(files)
        paths2 = CsvPaths()
        pm2 = paths2.paths_manager
        pm2.remove_all_named_paths()
        pm2.add_named_paths_from_dir(directory=DIR, name="many")
        assert pm2.total_named_paths() == 1
