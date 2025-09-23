import unittest
import os
from uuid import uuid4
from csvpath import CsvPaths
from csvpath.managers.paths.paths_manager import PathsManager
from csvpath.managers.paths.paths_listener import PathsListener
from csvpath.managers.paths.paths_metadata import PathsMetadata
from csvpath.util.nos import Nos
from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter
from tests.csvpaths.builder import Builder

DIR = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths"
JSON = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths.json"
PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}many.csvpaths"


class TestCsvPathsManagersPathsManager(unittest.TestCase):
    def test_paths_listener_1(self):
        paths = Builder().build()

        paths.config.set_config_path_and_reload(
            os.path.join(
                "assets",
                "config",
                "jenkins-windows-local.ini" if os.sep == "\\" else "config.ini",
            )
        )

        reg = PathsListener(paths)
        mdata = PathsMetadata(paths.config)
        mdata.named_paths_name = "aname"
        mdata.named_paths_home = os.path.join("root", "aname")
        mdata.group_file_path = os.path.join("root", "aname", "group.csvpaths")
        mdata.source_path = "a/b/c"
        mdata.fingerprint = "123"
        mdata.manifest_path = os.path.join("root", "aname", "manifest.json")
        #
        # check mdata to mani transfer
        #
        mani = reg._prep_update(mdata)
        assert mani["paths_manifest"] == os.path.join("root", "aname", "manifest.json")
        assert mani["manifest_path"] == os.path.join(
            paths.config.get(section="inputs", name="csvpaths"), "manifest.json"
        )
        assert mani["uuid"] is not None
        assert mani["time"] is not None
        assert mani["paths_manifest"] == os.path.join("root", "aname", "manifest.json")
        assert mani["fingerprint"] == "123"
        assert mani["named_paths_name"] == "aname"
        assert mani["named_paths_home"] == os.path.join("root", "aname")
        assert mani["group_file_path"] == os.path.join(
            "root", "aname", "group.csvpaths"
        )
        assert mani["source_path"] == "a/b/c"
        assert mani["fingerprint"] == "123"

    def test_paths_listener_2(self):
        paths = Builder().build()
        grps = paths.config.get(section="listeners", name="groups")
        paths.add_to_config("listeners", "groups", "default")
        mani = paths.paths_manager.paths_root_manifest
        paths.paths_manager.add_named_paths(
            name="aname", paths=["$[*][yes()]"], source_path="a/b/c"
        )
        mani2 = paths.paths_manager.paths_root_manifest
        assert len(mani) + 1 == len(mani2)
        if grps is not None and isinstance(grps, str):
            paths.add_to_config("listeners", "groups", grps)

    def test_paths_create_definition_by_default(self):
        paths = Builder().build()
        paths.config.get(section="listeners", name="groups")
        paths.add_to_config("listeners", "groups", "default")
        name = "aname"
        p = "$[*][yes()]"
        paths.paths_manager.add_named_paths(name=name, paths=[p])
        definition = paths.paths_manager.get_json_paths_file(name)
        assert definition is not None
        assert isinstance(definition, dict)
        assert len(definition) == 1
        assert name in definition
        lst = definition[name]
        assert lst is not None
        assert isinstance(lst, list)
        assert len(lst) == 0

    def test_paths_manager_append_1(self):
        paths = Builder().build()
        paths.config.get(section="listeners", name="groups")
        paths.add_to_config("listeners", "groups", "default")
        paths.paths_manager.add_named_paths_from_file(
            name="aname",
            file_path=f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}people.csvpaths",
            append=False,
        )
        mdata1 = paths.paths_manager.last_add_metadata
        assert paths.paths_manager.has_named_paths("aname")
        assert len(paths.paths_manager.get_named_paths("aname")) == 2
        paths.paths_manager.add_named_paths_from_file(
            name="aname",
            file_path=f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}people.csvpaths",
            append=True,
        )
        mdata2 = paths.paths_manager.last_add_metadata
        assert paths.paths_manager.has_named_paths("aname")
        assert len(paths.paths_manager.get_named_paths("aname")) == 4
        #
        # we include all csvpaths in metadata when we append, not just the appended csvpaths
        #
        assert len(mdata2.named_paths) == 2 * len(mdata1.named_paths)

    def test_named_paths_add_and_external_change(self):
        name = f"{uuid4()}"
        apath = "$[*][yes()]"
        paths = Builder().build()
        paths.paths_manager.add_named_paths(name=name, paths=[apath])
        lst = CsvPaths().paths_manager.get_named_paths(name)
        assert lst
        assert len(lst) == 1
        assert lst[0].strip() == apath.strip()
        #
        # get named-paths manifest to count number of updates == 1
        #
        mani = CsvPaths().paths_manager.get_manifest_for_name(name)
        assert len(mani) == 1
        #
        # update the group.csvpaths file "by hand"
        #
        home = CsvPaths().paths_manager.named_paths_home(name)
        nos = Nos(home)
        assert nos.dir_exists()
        nos.path = os.path.join(home, "group.csvpaths")
        assert nos.exists()
        with DataFileReader(nos.path) as read:
            dfw = DataFileWriter(path=nos.path)
            t = read.read()
            t += " ~ test ~ "
            dfw.write(t)
        #
        # get paths to trigger the catch-up mani write. this is what
        # we're testing.
        #
        paths = CsvPaths().paths_manager.get_named_paths(name)
        assert paths
        assert len(paths) == 1
        #
        # check the mani len
        #
        mani = CsvPaths().paths_manager.get_manifest_for_name(name)
        assert len(mani) == 2
        #
        # clean up
        #
        CsvPaths().paths_manager.remove_named_paths(name)
        lst = CsvPaths().paths_manager.get_named_paths(name)
        assert lst is None

    def test_named_paths_adda(self):
        name = f"{uuid4()}"
        apath = "$[*][yes()]"
        paths = Builder().build()
        paths.paths_manager.add_named_paths(name=name, paths=[apath])
        lst = CsvPaths().paths_manager.get_named_paths(name)
        assert lst
        assert len(lst) == 1
        assert lst[0].strip() == apath.strip()
        CsvPaths().paths_manager.remove_named_paths(name)
        lst = CsvPaths().paths_manager.get_named_paths(name)
        assert lst is None

    def test_named_paths_add_to_existing(self):
        apath = "$[*][yes()]"
        paths = Builder().build()
        name = "test_add_to_existing"
        if paths.paths_manager.has_named_paths("test_add_to_existing"):
            paths.paths_manager.remove_named_paths(name)
        #
        # add one
        #
        paths.paths_manager.add_named_paths(name=name, paths=[apath])
        lst = Builder().build().paths_manager.get_named_paths(name)
        assert lst
        assert len(lst) == 1
        assert lst[0].strip() == apath.strip()
        #
        # add another on top
        #
        paths.paths_manager.add_named_paths(name=name, paths=[apath], append=True)
        lst = Builder().build().paths_manager.get_named_paths(name)
        assert lst
        assert len(lst) == 2
        assert lst[0].strip() == apath.strip()
        assert lst[1].strip() == apath.strip()

        Builder().build().paths_manager.remove_named_paths(name)
        lst = Builder().build().paths_manager.get_named_paths(name)
        assert lst is None

    def test_named_paths_set_named_paths1(self):
        paths = Builder().build()
        paths.file_manager.add_named_file(
            name="test",
            path=f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}test.csv",
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
        paths = Builder().build()
        pm = paths.paths_manager
        pm.remove_all_named_paths()
        pm.add_named_paths_from_json(file_path=JSON)
        assert pm.has_named_paths("many")
        assert pm.has_named_paths("numbers")
        assert pm.has_named_paths("needs split")
        assert pm.number_of_named_paths("numbers") == 3
        assert pm.number_of_named_paths("needs split") == 1

    def test_named_paths_dict1(self):
        paths = Builder().build()
        pm = paths.paths_manager
        np = ["~name:wonderful~$[*][yes()]", "~id:amazing~$[*][yes()]"]
        i = pm.total_named_paths()
        if i > 0 and pm.has_named_paths("many"):
            pm.remove_named_paths("many")
            j = pm.total_named_paths()
            assert j == i - 1
        i = pm.total_named_paths()
        pm.add_named_paths(name="many", paths=np)
        assert pm.total_named_paths() == i + 1
        assert pm.has_named_paths("many")
        assert pm.number_of_named_paths("many") == 2

    def test_named_paths_dict2(self):
        paths = Builder().build()
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
        paths = Builder().build()
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

        paths = pm.get_named_paths("$many.csvpaths.:1")
        assert len(paths) == 1
        assert paths[0].find("#2") > -1

    # need:
    # . all in directory under one name
    # . add duplicates to name
    def test_named_paths_dir(self):
        paths = Builder().build()
        pm = paths.paths_manager
        pm.remove_all_named_paths()
        assert pm.total_named_paths() == 0
        pm.add_named_paths_from_dir(directory=DIR)
        files = os.listdir(DIR)
        files = [f for f in files if f.find("csvpath") > -1]
        assert pm.total_named_paths() == len(files)
        paths2 = Builder().build()
        pm2 = paths2.paths_manager
        pm2.remove_all_named_paths()
        pm2.add_named_paths_from_dir(directory=DIR, name="many")
        assert pm2.total_named_paths() == 1
