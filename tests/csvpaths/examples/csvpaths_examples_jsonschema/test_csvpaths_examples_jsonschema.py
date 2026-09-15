import unittest
import pytest
import os

from tests.csvpaths.builder import Builder
from csvpath.util.file_readers import DataFileReader
from csvpath.matching.util.exceptions import MatchException
from csvpath.util.nos import Nos

SCHEMA = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_jsonschema{os.sep}automobiles.jsonschema"
GOOD = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_jsonschema{os.sep}automobiles.json"
BAD = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_jsonschema{os.sep}automobiles_bad.json"
PATHS = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_jsonschema{os.sep}automobiles.csvpaths"


class TestCsvPathsExamplesJsonSchema(unittest.TestCase):
    def test_csvpaths_jsonschema_1(self):
        name = "TestCsvPathsExamplesJsonSchema"
        paths = Builder().build()
        paths.config.set(section="errors", name="csvpaths", value="fail,print,raise")
        paths.paths_manager.add_named_paths(name=name, from_file=PATHS)
        text = None
        with DataFileReader(SCHEMA) as reader:
            text = reader.source.read()
        paths.paths_manager.asset_manager.store_asset_file(
            name=name, filename="automobiles.jsonschema", contents=text
        )
        paths.file_manager.add_named_file(name=name, path=GOOD)
        ref = paths.collect_paths(pathsname=name, filename=name)
        results = paths.results_manager.get_named_results(ref)
        assert results is not None
        assert len(results) == 1
        assert results[0].csvpath
        assert results[0].csvpath.is_valid

        #
        # make sure the data.json file gets created and the data.csv
        # is not produced
        #
        rundir = results[0].run_dir
        instance = Nos(rundir).join("0")
        data = Nos(instance).join("data.json")
        assert Nos(data).exists()
        data = Nos(instance).join("data.csv")
        assert not Nos(data).exists()

        paths.paths_manager.remove_named_paths(name)
        paths.file_manager.remove_named_file(name)

    def test_csvpaths_jsonschema_2(self):
        name = "TestCsvPathsExamplesJsonSchema"
        paths = Builder().build()
        paths.config.set(section="errors", name="csvpaths", value="fail,print,no-raise")
        paths.paths_manager.add_named_paths(name=name, from_file=PATHS)
        text = None
        with DataFileReader(SCHEMA) as reader:
            text = reader.source.read()
        paths.paths_manager.asset_manager.store_asset_file(
            name=name, filename="automobiles.jsonschema", contents=text
        )
        paths.file_manager.add_named_file(name=name, path=BAD)
        ref = paths.collect_paths(pathsname=name, filename=name)
        results = paths.results_manager.get_named_results(ref)
        assert results is not None
        assert len(results) == 1
        assert results[0].csvpath
        assert not results[0].csvpath.is_valid
        paths.paths_manager.remove_named_paths(name)
        paths.file_manager.remove_named_file(name)

    def test_csvpaths_jsonschema_3(self):
        name = "TestCsvPathsExamplesJsonSchema"
        paths = Builder().build()
        paths.config.set(section="errors", name="csvpaths", value="fail,print,raise")
        paths.paths_manager.add_named_paths(name=name, from_file=PATHS)
        text = None
        with DataFileReader(SCHEMA) as reader:
            text = reader.source.read()
        paths.paths_manager.asset_manager.store_asset_file(
            name=name, filename="automobiles.jsonschema", contents=text
        )
        paths.file_manager.add_named_file(name=name, path=BAD)
        with pytest.raises(MatchException):
            paths.collect_paths(pathsname=name, filename=name)

        paths.paths_manager.remove_named_paths(name)
        paths.file_manager.remove_named_file(name)
