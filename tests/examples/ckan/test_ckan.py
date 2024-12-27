import unittest
import os
from csvpath import CsvPaths
from csvpath.managers.results.results_metadata import ResultsMetadata
from csvpath.managers.integrations.ckan.dataset import Dataset
from csvpath.managers.integrations.ckan.ckan_listener import CkanListener


class TestJsonNamedPaths(unittest.TestCase):
    def test_ckan_visibility(self):
        paths = CsvPaths()
        paths.file_manager.add_named_files_from_dir("tests/examples/ckan/csvs")
        paths.paths_manager.add_named_paths_from_dir(
            name="ckantest", directory="tests/examples/ckan/csvpaths"
        )
        paths.collect_paths(filename="March-2024", pathsname="ckantest")
        r = paths.results_manager.get_specific_named_result("ckantest", "upc-sku")
        dataset = Dataset(listener=None, manifest=None, metadata=None)
        lst = CkanListener()
        #
        # visibility
        #
        lst._set_visibility(dataset, r)
        assert dataset.visible is False

    def test_ckan_group(self):
        paths = CsvPaths()
        paths.file_manager.add_named_files_from_dir("tests/examples/ckan/csvs")
        paths.paths_manager.add_named_paths_from_dir(
            name="ckantest", directory="tests/examples/ckan/csvpaths"
        )
        paths.collect_paths(filename="March-2024", pathsname="ckantest")
        r = paths.results_manager.get_specific_named_result("ckantest", "upc-sku")
        # Dataset(listener=None, manifest=None, metadata=None)
        lst = CkanListener()
        #
        # group name
        #
        mdata = ResultsMetadata(r.csvpath.csvpaths.config)
        group, title = lst._get_group_name(r, mdata)
        assert group is not None
        assert group == "a big test"
        assert title == "A Big Test"

        r.csvpath.metadata["ckan-group"] = "use-archive"
        mdata.archive_name = "Fish"
        group, title = lst._get_group_name(r, mdata)
        assert group is not None
        assert group == "fish"
        assert title == "Fish"

        r.csvpath.metadata["ckan-group"] = "use-named-results"
        mdata.named_results_name = "ckantest"
        group, title = lst._get_group_name(r, mdata)
        assert group is not None
        assert group == "ckantest"
        assert title == "ckantest"

    def test_ckan_publish(self):
        paths = CsvPaths()
        paths.file_manager.add_named_files_from_dir("tests/examples/ckan/csvs")
        paths.paths_manager.add_named_paths_from_dir(
            name="ckantest", directory="tests/examples/ckan/csvpaths"
        )
        paths.collect_paths(filename="March-2024", pathsname="ckantest")
        r = paths.results_manager.get_specific_named_result("ckantest", "upc-sku")
        # Dataset(listener=None, manifest=None, metadata=None)
        lst = CkanListener()
        #
        # publish
        #
        results = paths.results_manager.get_named_results("ckantest")
        r.csvpath.metadata["ckan-publish"] = "never"
        b = lst._publish(result=r, results=results)
        assert b is False

        r.csvpath.metadata["ckan-publish"] = "always"
        b = lst._publish(result=r, results=results)
        assert b is True

        r.csvpath.metadata["ckan-publish"] = "on-valid"
        b = lst._publish(result=r, results=results)
        assert b is False  # we're not valid, right?

        r.csvpath._is_valid = True
        b = lst._publish(result=r, results=results)
        assert b is True
        r.csvpath._is_valid = False

        r.csvpath.metadata["ckan-publish"] = "on-all-valid"
        b = lst._publish(result=r, results=results)
        assert b is False

        for r2 in results:
            r2._is_valid = True
        r.csvpath._is_valid = True

        r.csvpath.metadata["ckan-publish"] = "on-all-valid"
        b = lst._publish(result=r, results=results)
        assert b is True

    #
    # TODO: remaining 4 vvvvv
    #

    def test_ckan_dataset_name(self):
        paths = CsvPaths()
        paths.file_manager.add_named_files_from_dir("tests/examples/ckan/csvs")
        paths.paths_manager.add_named_paths_from_dir(
            name="ckantest", directory="tests/examples/ckan/csvpaths"
        )
        paths.collect_paths(filename="March-2024", pathsname="ckantest")
        r = paths.results_manager.get_specific_named_result("ckantest", "upc-sku")
        dataset = Dataset(listener=None, manifest=None, metadata=None)
        lst = CkanListener()
        #
        # dataset name/title
        #
        mdata = ResultsMetadata(r.csvpath.csvpaths.config)
        mdata.named_results_name = "is-nr-name"
        r.csvpath.metadata["ckan-dataset-name"] = "a-b-c"
        lst._set_dataset_name(dataset=dataset, result=r, mani=None, mdata=mdata)
        assert dataset.name == "a-b-c"
        r.csvpath.metadata["ckan-dataset-name"] = "use-named-results"
        lst._set_dataset_name(dataset=dataset, result=r, mani=None, mdata=mdata)
        assert dataset.name == "is-nr-name"
        r.csvpath.metadata["ckan-dataset-name"] = "use-instance"
        lst._set_dataset_name(dataset=dataset, result=r, mani=None, mdata=mdata)
        assert dataset.name == "upc-sku"
        r.csvpath.metadata["ckan-dataset-name"] = "var-value:name"
        assert "name" in r.csvpath.variables
        lst._set_dataset_name(dataset=dataset, result=r, mani=None, mdata=mdata)
        assert dataset.name == "this is a var value"

    def test_ckan_tags(self):
        paths = CsvPaths()
        paths.file_manager.add_named_files_from_dir("tests/examples/ckan/csvs")
        paths.paths_manager.add_named_paths_from_dir(
            name="ckantest", directory="tests/examples/ckan/csvpaths"
        )
        paths.collect_paths(filename="March-2024", pathsname="ckantest")
        r = paths.results_manager.get_specific_named_result("ckantest", "upc-sku")
        dataset = Dataset(listener=None, manifest=None, metadata=None)
        lst = CkanListener()
        mdata = ResultsMetadata(r.csvpath.csvpaths.config)
        #
        # tags
        #
        mdata.run_home = r.instance_dir
        r.csvpath.metadata[
            "ckan-tags"
        ] = "instance-identity, instance-home, var-value:name, mouse"
        lst._set_tags(dataset=dataset, result=r, mdata=mdata)
        assert {"name": "this is a var value"} in dataset.tags
        assert {"name": "upc-sku"} in dataset.tags
        assert {"name": "mouse"} in dataset.tags
        i = 0
        for t in dataset.tags:
            if t["name"].endswith("upc-sku"):
                i += 1
        assert i == 2

    def test_ckan_fields(self):
        paths = CsvPaths()
        paths.file_manager.add_named_files_from_dir("tests/examples/ckan/csvs")
        paths.paths_manager.add_named_paths_from_dir(
            name="ckantest", directory="tests/examples/ckan/csvpaths"
        )
        paths.collect_paths(filename="March-2024", pathsname="ckantest")
        r = paths.results_manager.get_specific_named_result("ckantest", "upc-sku")
        dataset = Dataset(listener=None, manifest=None, metadata=None)
        lst = CkanListener()
        #
        # fields
        #
        r.csvpath.metadata["ckan-show-fields"] = "var-value:name, line_number"
        lst._set_metadata_fields(dataset=dataset, result=r)
        assert {"key": "name", "value": "this is a var value"} in dataset.fields
        assert {"key": "line_number", "value": "15"} in dataset.fields

    # ------------------------------
    #
    #
    # TODO: refactor send files and create tests
    #
