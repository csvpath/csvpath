import unittest
import pytest
import os
import json
from datetime import datetime
from csvpath.managers.results.result import Result
from csvpath.managers.results.result_serializer import ResultSerializer
from csvpath.util.nos import Nos
from csvpath.util.file_readers import DataFileReader
from tests.csvpaths.builder import Builder

FOODX = (
    f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files{os.sep}foodx.csv"
)
PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files{os.sep}food.csv"
FILES = {"food": PATH}

NAMED_PATHS_DIR = (
    f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}"
)
FILES_DIR = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files"


class TestCsvPathsManagersResultsManager(unittest.TestCase):
    def test_unknown_results(self) -> None:
        paths = Builder().build()
        name = "unknown__"
        r = paths.results_manager.get_errors(name)
        assert not r
        r = paths.results_manager.get_metadata(name)
        assert not r
        r = paths.results_manager.get_variables(name)
        assert not r
        r = paths.results_manager.get_printouts(name)
        assert not r

    def test_results_mgr1(self):
        paths = Builder().build()
        paths.config.add_to_config("results", "archive", "this doesn't exist")
        #
        # this method must return an empty list and write a log warning. it cannot blowup.
        #
        paths.results_manager.list_named_results()

    def test_results_print_to_printouts(self):
        paths = Builder().build()
        paths.file_manager.add_named_files_from_dir(
            f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files"
        )
        paths.paths_manager.add_named_paths(
            name="print_test",
            paths=[
                """$[3][
                        print("my msg", "error")
                        print("my other msg", "foo-bar")
                        print("hello world")
                   ]"""
            ],
        )

        paths.fast_forward_paths(pathsname="print_test", filename="food")
        results = paths.results_manager.get_named_results("print_test")
        assert results
        assert len(results) == 1
        ps = results[0].get_printouts("error")
        assert len(ps) == 1
        assert ps[0].find("my msg") > -1
        ps = results[0].get_printouts("foo-bar")
        assert len(ps) == 1
        assert ps[0].find("my other msg") > -1
        printouts = paths.results_manager.get_printouts("print_test")
        assert printouts
        assert len(printouts) == len(results[0].get_printouts())

    def test_results_save_1(self):
        # archive dir in cwd. we'll put it in directly below because
        # results seralizer only uses it to feed back to a method that
        # calls save() where we're passing it in.
        rs = ResultSerializer("archive")
        meta = {"meta": "hi"}
        run = {}
        errors = [{}]
        variables = {"my_var": 23}
        lines = [["test", "test2", "test3"], ["test4", "test5", "test6"]]
        printouts = {"default": ["this is an output", "also an output"]}
        paths_name = "test_namedpaths_name"
        identity = "test_identity"
        rs._save(
            metadata=meta,
            runtime_data=run,
            errors=errors,
            variables=variables,
            lines=lines,
            printouts=printouts,
            paths_name=paths_name,
            file_name="my.csv",
            identity=identity,
            run_time=datetime.now(),
            run_index=1,
            run_dir="archive",
            unmatched=[],
        )

    def test_results_save_error(self):
        paths = Builder().build()
        paths.file_manager.add_named_files_from_dir(FILES_DIR)
        paths.paths_manager.add_named_paths(
            name="print_test",
            paths=[
                """
                ~ validation-mode: no-raise, print
                $[3][
                    add( "test", none() )
                ]"""
            ],
        )
        paths.fast_forward_paths(pathsname="print_test", filename="food")
        results = paths.results_manager.get_named_results("print_test")
        assert results

    def test_result_instance_manifest_persists_error_count(self):
        # issue #227: error_count is computed by ResultRegistrar.
        # register_complete() but was never written into the Result
        # Instance Manifest by metadata_update() -- confirms the fix.
        paths = Builder().build()
        paths.file_manager.add_named_files_from_dir(FILES_DIR)
        paths.paths_manager.add_named_paths(
            name="error_count_test",
            paths=[
                """
                ~ validation-mode: no-raise, print
                $[3][
                    add( "test", none() )
                ]"""
            ],
        )
        paths.fast_forward_paths(pathsname="error_count_test", filename="food")
        results = paths.results_manager.get_named_results("error_count_test")
        assert results
        result = results[0]
        assert result.errors_count > 0

        m = Nos(result.instance_dir).join("manifest.json")
        with DataFileReader(m) as file:
            js = json.load(file.source)
        assert js["error_count"] == result.errors_count

    def test_result_instance_manifest_persists_method(self):
        # method is set on ResultMetadata but was never written into the
        # Result Instance Manifest by ResultRegistrar.metadata_update() --
        # confirms the fix (same bug shape as error_count / issue #227).
        paths = Builder().build()
        paths.file_manager.add_named_files_from_dir(FILES_DIR)
        paths.paths_manager.add_named_paths(
            name="method_persist_test",
            paths=[""" ~ validation-mode: no-raise, print~ $[3][ print( "test" ) ]"""],
        )
        paths.fast_forward_paths(pathsname="method_persist_test", filename="food")
        results = paths.results_manager.get_named_results("method_persist_test")
        assert results
        result = results[0]

        m = Nos(result.instance_dir).join("manifest.json")
        with DataFileReader(m) as file:
            js = json.load(file.source)
        assert js["method"] == "fast_forward_paths"

    def test_results_run_manifest_persists_template(self):
        # template was never captured on ResultsMetadata at all, so the
        # per-run manifest.json in the run_dir (Results Run Manifest,
        # table 5) never had a "template" key, unlike the archive-root
        # ledger manifest (table 7, see test_results_template_captured).
        paths = Builder().build()
        paths.file_manager.add_named_file(name="food", path=PATH)
        paths.paths_manager.add_named_paths(
            name="run_template_capture",
            paths=[""" ~ validation-mode: no-raise, print~ $[0][ print( "test" ) ]"""],
        )
        paths.fast_forward_paths(
            pathsname="run_template_capture", filename="food", template=":0/:run_dir"
        )
        results = paths.results_manager.get_named_results("run_template_capture")
        assert results
        result = results[0]

        m = Nos(result.run_dir).join("manifest.json")
        with DataFileReader(m) as file:
            js = json.load(file.source)
        assert js["template"] == ":0/:run_dir"

    def test_results_template_captured(self):
        paths = Builder().build()

        a = paths.config.get(section="results", name="archive")
        print(f"archive: {a}")

        paths.file_manager.add_named_file(name="food", path=PATH)
        paths.paths_manager.add_named_paths(
            name="template_capture",
            paths=[""" ~ validation-mode: no-raise, print~ $[0][ print( "test" ) ]"""],
        )
        paths.fast_forward_paths(
            pathsname="template_capture", filename="food", template=":0/:run_dir"
        )
        results = paths.results_manager.get_named_results("template_capture")
        assert results

        m = Nos(a).join("manifest.json")
        with DataFileReader(m) as file:
            js = json.load(file.source)
            for _ in js:
                assert "template" in _

    def test_results_named_results_home(self):
        paths = Builder().build()
        paths.file_manager.add_named_file(name="foodx", path=FOODX)
        paths.paths_manager.add_named_paths(
            name="print_test",
            paths=[
                """ ~ validation-mode: print
                        $[3][ add( 3, 3 ) ]"""
            ],
        )
        ref = paths.fast_forward_paths(pathsname="print_test", filename="foodx")
        assert ref
        assert isinstance(ref, str)
        results = paths.results_manager.get_named_results("print_test")
        assert results
        path = paths.results_manager.get_named_results_home(ref)
        assert path
        assert path.find(ref) == -1
        results2 = paths.results_manager.get_named_results(ref)
        assert results2
        assert len(results2) == len(results)
        assert str(results2[0].run_uuid) == str(results[0].run_uuid)

    def test_results_mgr_specific_named_result(self):
        paths = Builder().build()

        from tests.conftest import _clear_files

        _clear_files()

        path = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}food.csvpaths"
        if paths.paths_manager.has_named_paths("food"):
            paths.paths_manager.remove_named_paths("food")
        paths.paths_manager.add_named_paths(name="food", from_file=path)

        path = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files{os.sep}food.csv"
        if paths.file_manager.has_named_file("food"):
            paths.file_manager.remove_named_file("food")
        paths.file_manager.add_named_file(name="food", path=path)

        paths.collect_paths(filename="food", pathsname="food")

        with pytest.raises(ValueError):
            paths.results_manager.get_specific_named_result("food")

        ref = "$food#candy check.results.:0"
        result = paths.results_manager.get_specific_named_result(ref)
        # if result is None:
        #    pytest.exit("Cannot find {ref}")

        assert result is not None
        assert isinstance(result, Result)
        assert result.csvpath.identity == "candy check"

        ref = "$food.results.2025.candy check"
        result = paths.results_manager.get_specific_named_result(ref)
        # if result is None:
        #    pytest.exit("Cannot find {ref}")

        assert result is not None
        assert isinstance(result, Result)
        assert result.csvpath.identity == "candy check"

        with pytest.raises(ValueError):
            paths.results_manager.get_specific_named_result("$food.results.candy check")
