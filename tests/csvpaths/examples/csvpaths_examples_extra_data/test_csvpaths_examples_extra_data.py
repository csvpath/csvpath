import unittest
import os
import json

from csvpath.managers.results.results_registrar import ResultsRegistrar
from csvpath.util.nos import Nos
from csvpath.util.file_readers import DataFileReader

from tests.csvpaths.builder import Builder

CSV = os.path.join(
    "tests",
    "csvpaths",
    "examples",
    "csvpaths_examples_extra_data",
    "csvs",
    "March-2024.csv",
)
PATH = os.path.join(
    "tests",
    "csvpaths",
    "examples",
    "csvpaths_examples_extra_data",
    "csvpaths",
    "extra.csvpath",
)


class TestCsvPathsExamplesExtraData(unittest.TestCase):
    def test_save_extra_data_1(self):
        paths = Builder().build()
        rr = ResultsRegistrar(csvpaths=paths, run_dir=None, pathsname=None)
        path = os.path.join(
            "tests",
            "csvpaths",
            "examples",
            "csvpaths_examples_extra_data",
            "extra.json",
        )
        nos = Nos(path)
        if nos.exists():
            nos.remove()

        extra = {"test": "value"}
        rr._save_extra_data(path, extra)

        assert nos.exists()
        with DataFileReader(path) as reader:
            j = json.load(reader.source)
            assert j == extra
        extra["test2"] = "foo"
        rr._save_extra_data(path, extra)

        assert nos.exists()
        with DataFileReader(path) as reader:
            j = json.load(reader.source)
            assert j == extra
        nos.remove()

    def test_save_extra_data_2(self):
        paths = Builder().build()
        paths.config.set(
            section="errors", name="csvpaths", value="raise, collect, print"
        )
        paths.config.set(
            section="errors", name="csvpath", value="raise, collect, print"
        )
        #
        # clear and add files
        #
        if paths.file_manager.has_named_file("extra"):
            paths.file_manager.remove_named_file("extra")
        assert not paths.file_manager.has_named_file("extra")
        paths.file_manager.add_named_file(name="extra", path=CSV)
        assert paths.file_manager.has_named_file("extra")

        #
        # clear and add paths
        #
        if paths.paths_manager.has_named_paths("extra"):
            paths.paths_manager.remove_named_paths("extra")
        assert not paths.paths_manager.has_named_paths("extra")
        paths.paths_manager.add_named_paths(name="extra", from_file=PATH)
        #
        # run paths vs files
        #
        extra = {"my additional data": "12345"}
        ref = paths.collect_paths(filename="extra", pathsname="extra", extra_data=extra)
        #
        # check that we have the extra
        #
        results = paths.results_manager.get_named_results(ref)
        assert results is not None
        assert len(results) == 1
        run_dir = results[0].run_dir

        nos = Nos(run_dir)
        path = nos.join("_extra_data")
        path = Nos(path).join("extra.json")

        assert Nos(path).exists()
        with DataFileReader(path) as reader:
            j = json.load(reader.source)
            assert j == extra
