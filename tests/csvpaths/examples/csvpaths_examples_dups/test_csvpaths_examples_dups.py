import unittest
import pytest
import os
from csvpath import CsvPaths
from csvpath.util.exceptions import FileException
from csvpath.util.file_readers import DataFileReader


class TestDups(unittest.TestCase):
    def test_csvpaths_examples_dups(self):
        paths = CsvPaths()
        paths.config.set_config_path_and_reload(
            os.path.join(
                "tests",
                "csvpaths",
                "examples",
                "csvpaths_examples_dups",
                "dups_config.ini",
            )
        )
        #
        # add named file
        #
        name = "dups"
        path = os.path.join(
            "tests",
            "csvpaths",
            "examples",
            "csvpaths_examples_dups",
            "orders.csv",
        )
        paths.file_manager.remove_named_file(name)
        assert not paths.file_manager.has_named_file(name)
        paths.file_manager.add_named_file(name=name, path=path)
        assert paths.file_manager.has_named_file(name)
        #
        # add named paths
        #
        path = os.path.join(
            "tests", "csvpaths", "examples", "csvpaths_examples_dups", "orders.csvpath"
        )
        paths.paths_manager.remove_named_paths(name)
        assert not paths.paths_manager.has_named_paths(name)
        paths.paths_manager.add_named_paths_from_file(name=name, file_path=path)
        assert paths.paths_manager.has_named_paths(name)

        #
        # run
        #
        ref = paths.collect_paths(filename=name, pathsname=name)
        #
        # check the lookup data is loaded
        #
        results = paths.results_manager.get_named_results(name=ref)
        assert results
        assert len(results) == 2
        result = results[1]
        assert len(result.errors) == 0
        data = results[1].data_file_path
        assert data
        """
        with DataFileReader(data) as file:
            for _ in file.source:
                assert isinstance(_, str)
                assert int(_) > 0
                break
        """
        #
        # cleanup
        #
        paths.file_manager.remove_named_file(name)
        paths.paths_manager.remove_named_paths(name)
