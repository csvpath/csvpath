import unittest
import os

from tests.csvpaths.builder import Builder
from csvpath.runners.runner import Runner
from csvpath.util.file_readers import DataFileReader

SCHEMA = os.path.join(
    "tests", "csvpaths", "examples", "csvpaths_examples_dynamic", "test.schema.json"
)


SCHEMA_PATHS = os.path.join(
    "tests",
    "csvpaths",
    "examples",
    "csvpaths_examples_dynamic",
    "csvpaths",
    "schema.csvpath",
)

PATHS = os.path.join(
    "tests",
    "csvpaths",
    "examples",
    "csvpaths_examples_dynamic",
    "csvpaths",
    "dynamic.csvpath",
)

FILE = os.path.join(
    "tests",
    "csvpaths",
    "examples",
    "csvpaths_examples_dynamic",
    "files",
    "dynamic.txt",
)

DATA_ONE = [
    {"a": "fish", "b": "gull", "c": "clam"},
    {"a": "ant", "b": "mouse", "c": "dog"},
    {"a": "elephant", "b": "tiger", "c": "snake"},
]
DATA_ONE_B = [
    {"a": "breakfast", "b": "lunch", "c": "dinner"},
    {"a": "morning", "b": "afternoon", "c": "evening"},
    {"a": "large", "b": "medium", "c": "small"},
]


DATA_TWO = {
    "ocean": ["fish", "lobster", "clam"],
    "insect": ["ant", "spider", "flea"],
    "land": ["elephant", "tiger", "snake"],
}
DATA_THREE = [
    {
        "sky": ["bluebird", "bluejay", "blue-footed boobie"],
        "insect": ["ant", "spider", "flea"],
        "land": ["elephant", "tiger", "snake"],
    },
    {
        "ocean": ["fish", "lobster", "clam"],
        "insect": ["ant", "spider", "flea"],
        "land": ["elephant", "tiger", "snake"],
    },
    {
        "below": ["mole", "badger", "worm"],
        "insect": ["ant", "spider", "flea"],
        "land": ["elephant", "tiger", "snake"],
    },
]


class TestCsvPathsExamplesDynamic(unittest.TestCase):
    #
    # explicitly add named file.
    # collect dynamic doesn't set up, doesn't trust, doesn't register
    #
    def test_csvpaths_dynamic_jsonl_1(self):
        paths = Builder().build()

        #
        # clear any results
        #
        paths.results_manager.remove_named_results("dynamic")
        #
        # setup the named-file
        #
        paths.file_manager.add_named_file(name="dynamic", path=FILE)
        #
        # setup the named-paths
        #
        if paths.paths_manager.has_named_paths("dynamic"):
            paths.paths_manager.remove_named_paths("dynamic")
        paths.paths_manager.add_named_paths(name="dynamic", from_file=PATHS)

        #
        # run the data
        #
        refs = paths.collect_dynamic(
            pathsname="dynamic",
            dataname="dynamic",
            dataname_trust=False,
            data=DATA_ONE,
            shape=Runner.JSONL,
            register=False,
        )
        assert refs is not None
        assert len(refs) == 1
        ref = refs[0]

        results = paths.results_manager.get_named_results(ref)
        assert results is not None
        assert len(results) == 1
        assert results[0].is_valid

    #
    # implicitly add named file.
    # collect_dynamic sets up name, doesn't trust, does register
    #
    def test_csvpaths_dynamic_jsonl_2(self):
        paths = Builder().build()
        #
        # clear any results
        #
        paths.results_manager.remove_named_results("dynamic")
        #
        # remove the named-paths, if exists
        #
        if paths.file_manager.has_named_file("dynamic"):
            paths.file_manager.remove_named_file("dynamic")
        #
        # setup the named-paths
        #
        if paths.paths_manager.has_named_paths("dynamic"):
            paths.paths_manager.remove_named_paths("dynamic")
        paths.paths_manager.add_named_paths(name="dynamic", from_file=PATHS)

        #
        # run the data. named-file created in background.
        #
        refs = paths.collect_dynamic(
            pathsname="dynamic",
            dataname="dynamic",
            data=DATA_ONE,
            shape=Runner.JSONL,
            register=True,
            register_path=FILE,
        )
        assert refs is not None
        assert len(refs) == 1
        ref = refs[0]

        results = paths.results_manager.get_named_results(ref)
        assert results is not None
        assert len(results) == 1
        assert results[0].is_valid

    #
    # implicitly add named file. path not provided
    # collect_dynamic sets up name, doesn't trust,
    # doesn't register after the placeholder
    #
    def test_csvpaths_dynamic_jsonl_3(self):
        paths = Builder().build()
        #
        # clear any results
        #
        paths.results_manager.remove_named_results("dynamic")
        #
        # remove the named-paths, if exists. we wouldn't do this here if
        # this were not a unit test.
        #
        if paths.file_manager.has_named_file("dynamic"):
            paths.file_manager.remove_named_file("dynamic")
        #
        # setup the named-paths. we wouldn't do this here if not a unit test.
        # we could do it in flightpath
        #
        if paths.paths_manager.has_named_paths("dynamic"):
            paths.paths_manager.remove_named_paths("dynamic")
        paths.paths_manager.add_named_paths(name="dynamic", from_file=PATHS)

        #
        # run the data. named-file created in background.
        #
        refs = paths.collect_dynamic(
            pathsname="dynamic",
            dataname="dynamic",
            data=DATA_ONE,
            shape=Runner.JSONL,
            register=False,
        )
        assert refs is not None
        assert len(refs) == 1
        ref = refs[0]

        results = paths.results_manager.get_named_results(ref)
        assert results is not None
        assert len(results) == 1
        assert results[0].is_valid

    #
    # implicitly add named file. path not provided
    # collect_dynamic sets up name, doesn't trust,
    # registers
    #
    def test_csvpaths_dynamic_jsonl_4(self):
        paths = Builder().build()
        #
        # clear any results
        #
        paths.results_manager.remove_named_results("dynamic")
        #
        # remove the named-paths, if exists. we wouldn't do this here if
        # this were not a unit test.
        #
        if paths.file_manager.has_named_file("dynamic"):
            paths.file_manager.remove_named_file("dynamic")
        #
        # setup the named-paths. we wouldn't do this here if not a unit test.
        # we could do it in flightpath
        #
        if paths.paths_manager.has_named_paths("dynamic"):
            paths.paths_manager.remove_named_paths("dynamic")
        paths.paths_manager.add_named_paths(name="dynamic", from_file=PATHS)

        #
        # run the data. named-file created in background.
        #
        refs = paths.collect_dynamic(
            pathsname="dynamic",
            dataname="dynamic",
            data=DATA_ONE,
            shape=Runner.JSONL,
            register=True,
        )
        assert refs is not None
        assert len(refs) == 1
        ref = refs[0]
        refs = paths.collect_dynamic(
            pathsname="dynamic",
            dataname="dynamic",
            data=DATA_ONE_B,
            shape=Runner.JSONL,
            register=True,
        )
        results = paths.results_manager.get_named_results(ref)
        assert results is not None
        assert len(results) == 1
        assert results[0].is_valid

        results = paths.results_manager.get_runs_available("dynamic")
        print(f"resux: {results}")
        assert results is not None
        assert len(results) == 2

    #
    # implicitly add named file. path not provided
    # collect_dynamic sets up name, doesn't trust,
    # registers. treats list as list of jsons.
    #
    def test_csvpaths_dynamic_list_of_json_1(self):
        paths = Builder().build()
        #
        # clear any results
        #
        paths.results_manager.remove_named_results("dynamic")
        #
        # remove the named-paths, if exists. we wouldn't do this here if
        # this were not a unit test.
        #
        if paths.file_manager.has_named_file("dynamic"):
            paths.file_manager.remove_named_file("dynamic")
        #
        # setup the named-paths. we wouldn't do this here if not a unit test.
        # we could do it in flightpath
        #
        if paths.paths_manager.has_named_paths("dynamic"):
            paths.paths_manager.remove_named_paths("dynamic")
        paths.paths_manager.add_named_paths(name="dynamic", from_file=PATHS)

        #
        # run the data. named-file created in background.
        #
        refs = paths.collect_dynamic(
            pathsname="dynamic",
            dataname="dynamic",
            data=DATA_THREE,
            shape=Runner.LIST_OF_JSON,
            register=True,
        )
        assert refs is not None
        assert len(refs) == 3

        refs2 = paths.results_manager.get_runs_available("dynamic")
        assert len(refs2) == 3

        refs = paths.file_manager.get_named_file("$dynamic.files.:all")
        print(f"filesdrefs: {refs}")
        assert refs
        assert len(refs) == 3

    #
    # implicitly add named file. path not provided
    # collect_dynamic sets up name, doesn't trust,
    # registers. treats list as list of jsons.
    #
    def test_csvpaths_dynamic_list_of_json_2(self):
        paths = Builder().build()
        #
        # clear any results
        #
        paths.results_manager.remove_named_results("dynamic")
        #
        # remove the named-paths, if exists. we wouldn't do this here if
        # this were not a unit test.
        #
        if paths.file_manager.has_named_file("dynamic"):
            paths.file_manager.remove_named_file("dynamic")
        #
        # setup the named-paths. we wouldn't do this here if not a unit test.
        # we could do it in flightpath
        #
        if paths.paths_manager.has_named_paths("dynamic"):
            paths.paths_manager.remove_named_paths("dynamic")
        paths.paths_manager.add_named_paths(name="dynamic", from_file=PATHS)

        #
        # run the data. named-file created in background.
        #
        refs = paths.collect_dynamic(
            pathsname="dynamic",
            dataname="dynamic",
            data=DATA_THREE,
            shape=Runner.LIST_OF_JSON,
            register=False,
        )
        assert refs is not None
        assert len(refs) == 3

        refs2 = paths.results_manager.get_runs_available("dynamic")
        i = 0
        for r in refs2:
            try:
                _ = paths.results_manager.get_named_results(r)
                if _ is not None:
                    i += 1
            except Exception:
                ...
        assert i == 3

        refs = paths.file_manager.get_named_file("$dynamic.files.:all")
        refs = [refs] if isinstance(refs, str) else refs
        assert refs
        assert len(refs) == 1

    def test_csvpaths_dynamic_json_1(self):
        paths = Builder().build()

        #
        # create named paths
        #
        paths.paths_manager.add_named_paths(name="ffd", from_file=SCHEMA_PATHS)
        #
        # add json schema
        #
        with DataFileReader(SCHEMA) as reader:
            paths.paths_manager.asset_manager.store_asset_file(
                name="ffd", filename="test.schema.json", contents=reader.read()
            )

        #
        # do run
        #
        refs = paths.fast_forward_dynamic(
            pathsname="ffd",
            dataname="dynamic",
            data=DATA_TWO,
            shape=Runner.JSON,
            register=False,
        )
        assert refs
        assert len(refs) == 1
