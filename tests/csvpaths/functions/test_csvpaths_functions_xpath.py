import unittest
import os
from csvpath.matching.util.runtime_data_collector import RuntimeDataCollector

from tests.csvpaths.builder import Builder

FILE = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files{os.sep}zoo.xml"
PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}xpath.csvpath"


class TestCsvPathsFunctionsXPath(unittest.TestCase):
    def test_csvpaths_functions_xpath_1(self):
        paths = Builder().build()

        paths.paths_manager.add_named_paths_from_file(name="insert", file_path=PATH)
        paths.file_manager.add_named_file(name="insert", path=FILE)
        paths.collect_paths(pathsname="insert", filename="insert")
        results = paths.results_manager.get_named_results("insert")

        assert len(results) == 1
        result = results[0]
        assert result.errors_count == 0
        rd = {}
        RuntimeDataCollector.collect(result.csvpath, rd, local=True)

        assert rd
        assert rd.get("valid") is True
        v = result.variables
        print(f"v: {v}")
        assert v
        assert "animals" in v
        #
        # both unknown animals, as a list: a node-set of several gives a list
        #
        assert v["animals"] == ["Some kind of spotted cat", "A bear-like critter"]
