import unittest
import pytest
import os
from csvpath import CsvPaths
from csvpath.util.exceptions import FileException
from csvpath.util.file_readers import DataFileReader


class TestLookups(unittest.TestCase):

    #
    # commented out till we have a firm direction on header
    # value lookups.
    #
    def _test_ref_lookup(self):
        paths = CsvPaths()
        paths.config.set_config_path_and_reload(
            os.path.join(
                "tests",
                "csvpaths",
                "examples",
                "csvpaths_examples_lookups",
                "lookups_config.ini",
            )
        )
        #
        # add named file sic codes
        #
        sic_name = "sic-codes"
        path = os.path.join(
            "tests",
            "csvpaths",
            "examples",
            "csvpaths_examples_lookups",
            "sic-codes.csv",
        )
        paths.file_manager.remove_named_file(sic_name)
        assert not paths.file_manager.has_named_file(sic_name)
        paths.file_manager.add_named_file(name=sic_name, path=path)
        assert paths.file_manager.has_named_file(sic_name)
        #
        # add named paths sic codes lookup
        #
        lookup_name = "lookup"
        path = os.path.join(
            "tests",
            "csvpaths",
            "examples",
            "csvpaths_examples_lookups",
            "sic-lookup.csvpath",
        )
        paths.paths_manager.remove_named_paths(lookup_name)
        assert not paths.paths_manager.has_named_paths(lookup_name)
        paths.paths_manager.add_named_paths_from_file(name=lookup_name, file_path=path)
        assert paths.paths_manager.has_named_paths(lookup_name)

        #
        # add order file
        #
        orders_name = "orders"
        path = os.path.join(
            "tests",
            "csvpaths",
            "examples",
            "csvpaths_examples_lookups",
            "orders.csv",
        )
        paths.file_manager.remove_named_file(orders_name)
        assert not paths.file_manager.has_named_file(orders_name)
        paths.file_manager.add_named_file(name=orders_name, path=path)
        assert paths.file_manager.has_named_file(orders_name)
        #
        # add named paths orders
        #
        path = os.path.join(
            "tests",
            "csvpaths",
            "examples",
            "csvpaths_examples_lookups",
            "orders.csvpath",
        )
        paths.paths_manager.remove_named_paths(orders_name)
        assert not paths.paths_manager.has_named_paths(orders_name)
        paths.paths_manager.add_named_paths_from_file(name=orders_name, file_path=path)
        assert paths.paths_manager.has_named_paths(orders_name)

        #
        # load the sic codes
        #
        ref = paths.collect_paths(filename=sic_name, pathsname=lookup_name)
        #
        # check the lookup data is loaded
        #
        results = paths.results_manager.get_named_results(name=ref)
        assert results
        assert len(results) == 1
        result = results[0]
        assert len(result.errors) == 0
        data = results[0].data_file_path
        assert data
        with DataFileReader(data) as file:
            for _ in file.source:
                assert isinstance(_, str)
                assert int(_) > 0
                break
        #
        # do the orders
        #
        ref = paths.collect_paths(filename=orders_name, pathsname=orders_name)
        #
        # check 3 orders found
        #
        results = paths.results_manager.get_named_results(name=ref)
        assert results
        assert len(results) == 1
        data = results[0].data_file_path
        assert data
        with DataFileReader(data) as file:
            assert len(file.source) == 4

        #
        # cleanup
        #
        paths.file_manager.remove_named_file(sic_name)
        paths.paths_manager.remove_named_paths(lookup_name)
