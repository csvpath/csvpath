import unittest
import pytest
import shutil
import os
from csvpath import CsvPaths
from csvpath.managers.files.file_describer import NamedFileDescriber
from csvpath.util.nos import Nos
from tests.csvpaths.builder import Builder

FILE = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}test.csv"
FILE2 = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}test2.csv"


class TestCsvPathsManagersFileDescriber(unittest.TestCase):
    def test_files_describer_1(self) -> None:
        os.environ[
            "CSVPATH_CONFIG_PATH"
        ] = "tests/csvpaths/test_resources/generic_config.ini"
        paths = Builder().build()
        nf = "describer_test"
        #
        # clear out anything lingering
        #
        e = paths.file_manager.has_named_file(nf)
        if e is True:
            paths.file_manager.remove_named_file(nf)
        assert not e or not paths.file_manager.has_named_file(nf)
        #
        # test
        #
        describer = paths.file_manager.describer
        assert describer
        #
        # when we register a file a README should be created
        #
        paths.file_manager.add_named_file(name=nf, path=FILE)
        assert paths.file_manager.has_named_file(nf)
        path = os.path.join("tmp", "local", "inputs", "named_files", nf, "README.md")
        assert os.path.exists(path)
        #
        # update readme
        #
        describer = paths.file_manager.describer
        r = describer.get_readme(nf)
        assert r
        assert r.find("# Named") > -1
        r = "Modified!"
        describer.store_readme(nf, r)
        describer = paths.file_manager.describer
        r = describer.get_readme(nf)
        assert r.find("Mod") > -1
        #
        # update json
        #
        j = describer.get_json(nf)
        assert j == {}
        a = {
            describer.NAMED_PATHS_GROUP: "test_run",
            describer.RUN_TEMPLATE: "on_arrival_run_template",
        }
        j[describer.ON_ARRIVAL] = a
        describer.store_json(nf, j)
        j = describer.get_json(nf)
        assert describer.ON_ARRIVAL in j
        _ = j[describer.ON_ARRIVAL]
        assert a == _
        #
        # clear what we added
        #
        assert paths.file_manager.remove_named_file(nf)
        assert not paths.file_manager.has_named_file(nf)
        path = os.path.join("tmp", "local", "inputs", "named_files", nf)
        assert not os.path.exists(path)

    def test_files_activation_1(self) -> None:
        os.environ[
            "CSVPATH_CONFIG_PATH"
        ] = "tests/csvpaths/test_resources/generic_config.ini"
        paths = Builder().build()
        groups = paths.config.get(section="listeners", name="groups")
        if groups.find("activation") == -1:
            paths.config.set(
                section="listeners", name="groups", value="default, activation"
            )
        assert paths.config.get(section="listeners", name="activation.file")
        #
        #
        #
        np = "activation_test"
        nf = "activation_test"
        #
        # check describer exists. we need it to set up the activation
        #
        describer = paths.file_manager.describer
        assert describer
        #
        #
        #
        if paths.paths_manager.has_named_paths(np):
            paths.paths_manager.remove_named_paths(np)
        if paths.file_manager.has_named_file(nf):
            paths.file_manager.remove_named_file(nf)
        if paths.results_manager.has_named_results(np):
            paths.results_manager.remove_named_results(np)
        #
        # we register a file to create the named file. after it exists we
        # can setup the activation in order to handle new arrivals. since
        # it's a sure thing we want to know our named-file exists before
        # taking our hands off the wheel, this is a reasonable 1-2 way of
        # setting up.
        #
        paths.file_manager.add_named_file(name=nf, path=FILE)
        #
        # setup the activation
        #
        j = describer.get_json(nf)
        a = j.get(describer.ON_ARRIVAL)
        if a is None:
            a = {}
            j[describer.ON_ARRIVAL] = a
        a[describer.NAMED_PATHS_GROUP] = np
        #
        # seems that we get past the storing of the json before the add file listeners complete
        # when that happens we do a run in a way that is unhelpful.
        #
        import time

        time.sleep(0.5)
        #
        #
        #
        describer.store_json(nf, j)
        #
        # we need to emplace a named-path
        #
        paths.paths_manager.add_named_paths(name=np, paths=["$[*][@a = line_number()]"])
        #
        # register a new file on nf and the activation should happen
        #
        paths.file_manager.add_named_file(name=nf, path=FILE2)
        #
        # check for results. we're happening in a thread, so we may want to give
        # a brief pause
        #
        import time

        time.sleep(0.5)
        results = paths.results_manager.get_named_results(np)
        assert results
        assert len(results) == 1
        result = results[0]
        c = result.csvpath
        assert c
        a = c.variables.get("a")
        assert a is not None
