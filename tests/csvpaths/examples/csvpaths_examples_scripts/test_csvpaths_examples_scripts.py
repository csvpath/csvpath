import unittest
import pytest
import os
import platform
from csvpath import CsvPaths
from csvpath.managers.paths.paths_manager import PathsManager
from csvpath.util.nos import Nos

DIR = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths"
JSON = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths.json"
PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}many.csvpaths"


class TestCsvPathsExamplesPathsScripts(unittest.TestCase):
    def test_paths_mgr_script_run_1(self) -> None:
        paths = CsvPaths()
        #
        # set up config
        #
        paths.config.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.config.add_to_config("listeners", "groups", "scripts")
        paths.config.add_to_config("scripts", "run_scripts", "yes")
        #
        # setup paths
        #
        paths.paths_manager.add_named_paths_from_file(name="many", file_path=PATH)
        if platform.system() == "Windows":
            paths.paths_manager.store_script_for_paths(
                name="many",
                when="all",
                script_name="run.bat",
                text="echo 'hello world!'",
            )
        else:
            paths.paths_manager.store_script_for_paths(
                name="many",
                when="all",
                script_name="run.sh",
                text="echo 'hello world!'",
            )
        #
        # set up file
        #
        paths.file_manager.add_named_file(
            name="many",
            path=f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files{os.sep}food.csv",
        )
        #
        # we're using threads, but we worked around that with a box refactor, so not needed?
        #
        # paths.wrap_up_automatically = False
        #
        # run
        #
        paths.collect_paths(
            filename="many",
            pathsname="many",
        )
        #
        # get run_dir
        #
        results = paths.results_manager.get_named_results("many")
        assert results
        assert len(results) == 2
        out = results[0].run_dir
        #
        # list of (script_type, script_name)
        #
        lst = paths.paths_manager.get_scripts_for_paths("many")
        assert lst
        assert len(lst) == 1
        print(f"lstscripts: {lst}")
        #
        # check script exists
        #
        # first give the thread a chance to complete. would be nice
        # to have a better way, but this will do. it won't work for buckets
        # with their latency. otoh, i don't see an obviously right way to
        # support script running when the backend is not local. for now
        # it's going to be local-only.
        #
        import time

        time.sleep(0.5)
        assert paths.has_errors() is False
        #
        # check for output
        #
        p = os.path.join(out, lst[0][1])
        print(
            f"test_paths_mgr_script_run_1: p: {p}, {paths.config.get(section='scripts', name='run_scripts')}"
        )
        exists = Nos(p).exists()
        print(f"test_paths_mgr_script_run_1: p: {p}: {exists}")
        assert exists
        found = False
        files = Nos(out).listdir()
        for file in files:
            if file.startswith(lst[0][1]):
                found = True
        assert found is True
        paths.wrap_up()

    def test_paths_mgr_add_script_1(self) -> None:
        paths = CsvPaths()
        pm = paths.paths_manager
        name = "many"
        if pm.has_named_paths(name):
            home = pm.named_paths_home(name)
            for _ in PathsManager.SCRIPT_TYPES:
                script = os.path.join(home, _)
                nos = Nos(script)
                if nos.exists():
                    nos.remove()
        pm.add_named_paths_from_file(name=name, file_path=PATH)
        script_name = "many.sh"
        text = "echo 'hello world'"
        #
        # we're taking the default script type: on_complete_all_script, which
        # executes after every named-paths run, regardless of outcome
        #
        pm.store_script_for_paths(name=name, script_name=script_name, text=text)
        home = pm.named_paths_home(name)
        script = os.path.join(home, script_name)
        nos = Nos(script)
        assert nos.exists()
        s = pm.get_script_for_paths(name=name, script_type="on_complete_all_script")
        #
        # s will start with a shebang (assuming that is configured).
        #
        assert s.find(text) > -1

    def test_paths_mgr_add_script_2(self) -> None:
        paths = CsvPaths()
        pm = paths.paths_manager
        name = "many"
        if pm.has_named_paths(name):
            home = pm.named_paths_home(name)
            for _ in PathsManager.SCRIPT_TYPES:
                script = os.path.join(home, _)
                nos = Nos(script)
                if nos.exists():
                    nos.remove()
        pm.add_named_paths_from_file(name=name, file_path=PATH)
        script_name = "many.sh"
        #
        # bad script type
        #
        with pytest.raises(ValueError):
            pm.store_script_for_paths(
                name=name,
                when="after",
                script_name=script_name,
                text="echo 'hello world'",
            )

    def test_paths_mgr_add_script_3(self) -> None:
        paths = CsvPaths()
        pm = paths.paths_manager
        name = "many"
        if pm.has_named_paths(name):
            home = pm.named_paths_home(name)
            for _ in PathsManager.SCRIPT_TYPES:
                script = os.path.join(home, _)
                nos = Nos(script)
                if nos.exists():
                    nos.remove()
        pm.add_named_paths_from_file(name=name, file_path=PATH)
        #
        # bad script type
        #
        with pytest.raises(ValueError):
            pm.get_script_for_paths(name=name, script_type="on_complete_after_script")

    def test_paths_mgr_add_script_4(self) -> None:
        paths = CsvPaths()
        pm = paths.paths_manager
        name = "many"
        if pm.has_named_paths(name):
            home = pm.named_paths_home(name)
            for _ in PathsManager.SCRIPT_TYPES:
                script = os.path.join(home, _)
                nos = Nos(script)
                if nos.exists():
                    nos.remove()
        pm.add_named_paths_from_file(name=name, file_path=PATH)
        #
        # cannot give both script_type and when, even if they agree
        #
        with pytest.raises(ValueError):
            pm.store_script_for_paths(
                name=name,
                script_type="on_complete_all_script",
                when="all",
                script_name="test.sh",
            )
