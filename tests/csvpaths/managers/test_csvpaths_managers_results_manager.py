import unittest
import pytest
import os
from datetime import datetime
from csvpath import CsvPaths
from csvpath.managers.results.results_manager import ResultsManager
from csvpath.managers.results.result import Result
from csvpath.managers.results.result_serializer import ResultSerializer
from tests.csvpaths.builder import Builder


FOODX = (
    f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files{os.sep}foodx.csv"
)
FILES = {
    "food": f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files{os.sep}food.csv"
}
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
        paths.paths_manager.add_named_paths_from_dir(directory=NAMED_PATHS_DIR)
        paths.file_manager.set_named_files(FILES)

        paths.collect_paths(filename="food", pathsname="food")

        with pytest.raises(ValueError):
            paths.results_manager.get_specific_named_result("food")

        result = paths.results_manager.get_specific_named_result(
            "$food#candy check.results.:0"
        )
        assert result is not None
        assert isinstance(result, Result)
        assert result.csvpath.identity == "candy check"

        result = paths.results_manager.get_specific_named_result(
            "$food.results.2025.candy check"
        )
        assert result is not None
        assert isinstance(result, Result)
        assert result.csvpath.identity == "candy check"

        with pytest.raises(ValueError):
            paths.results_manager.get_specific_named_result("$food.results.candy check")
