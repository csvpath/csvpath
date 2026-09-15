import unittest
import pytest
import os
from csvpath.matching.util.exceptions import MatchException
from csvpath.util.file_readers import DataFileReader
from tests.csvpaths.builder import Builder

XSD = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_xsd{os.sep}automobiles.xsd"
GOOD = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_xsd{os.sep}automobiles.xml"
BAD = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_xsd{os.sep}automobiles_bad.xml"
PATHS = f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_xsd{os.sep}xsd.csvpaths"


class TestCsvPathsExamplesXsd(unittest.TestCase):
    def test_csvpaths_examples_xsd_1(self):
        name = "TestCsvPathsExamplesXsd"
        paths = Builder().build()
        paths.config.set(section="errors", name="csvpaths", value="fail,print,raise")
        paths.paths_manager.add_named_paths(name=name, from_file=PATHS)
        text = None
        with DataFileReader(XSD) as reader:
            text = reader.source.read()
        paths.file_manager.add_named_file(name=name, path=GOOD)
        paths.paths_manager.asset_manager.store_asset_file(
            name=name, filename="automobiles.xsd", contents=text
        )
        ref = paths.collect_paths(pathsname=name, filename=name)
        results = paths.results_manager.get_named_results(ref)
        assert results is not None
        assert len(results) == 1
        assert results[0].csvpath
        assert results[0].csvpath.is_valid

        paths.paths_manager.remove_named_paths(name)
        paths.file_manager.remove_named_file(name)

    def test_csvpaths_examples_xsd_2(self):
        name = "TestCsvPathsExamplesXsd"
        paths = Builder().build()
        paths.config.set(section="errors", name="csvpaths", value="fail,print,no-raise")
        paths.paths_manager.add_named_paths(name=name, from_file=PATHS)
        text = None
        with DataFileReader(XSD) as reader:
            text = reader.source.read()
        paths.file_manager.add_named_file(name=name, path=BAD)
        paths.paths_manager.asset_manager.store_asset_file(
            name=name, filename="automobiles.xsd", contents=text
        )
        ref = paths.collect_paths(pathsname=name, filename=name)
        results = paths.results_manager.get_named_results(ref)
        assert results is not None
        assert len(results) == 1
        assert results[0].csvpath
        assert not results[0].csvpath.is_valid
        paths.paths_manager.remove_named_paths(name)
        paths.file_manager.remove_named_file(name)

    def test_csvpaths_examples_xsd_3(self):
        name = "TestCsvPathsExamplesXsd"
        paths = Builder().build()
        paths.config.set(section="errors", name="csvpaths", value="fail,print,raise")
        paths.paths_manager.add_named_paths(name=name, from_file=PATHS)
        text = None
        with DataFileReader(XSD) as reader:
            text = reader.source.read()
        paths.file_manager.add_named_file(name=name, path=BAD)
        paths.paths_manager.asset_manager.store_asset_file(
            name=name, filename="automobiles.xsd", contents=text
        )
        with pytest.raises(MatchException):
            paths.collect_paths(pathsname=name, filename=name)
        paths.paths_manager.remove_named_paths(name)
        paths.file_manager.remove_named_file(name)
