import unittest
import os
from datetime import datetime
from csvpath import CsvPaths
from csvpath.managers.results.results_manager import ResultsManager
from csvpath.managers.results.result import Result
from csvpath.managers.results.result_serializer import ResultSerializer


class TestResultsManager(unittest.TestCase):
    def test_results_mgr2(self):
        # set up a csvpaths that will have 1 file and 1 set of paths
        filename = "food"
        pathsname = "many"
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        # get a csvpath. the csvpaths is not 100% configured but we don't need it.
        path = paths.csvpath()
        run_dir = os.path.join(paths.config.archive_name, pathsname)
        run_dir = os.path.join(run_dir, "arunid")
        # create a result as if we'd run paths against file
        result = Result(
            lines=[],
            csvpath=path,
            file_name=filename,
            paths_name=pathsname,
            run_index=1,
            run_time=None,
            run_dir=run_dir,
        )
        results = [result]
        rs = {}
        rs[pathsname] = results

        # set the results in the paths results manager. this replaces any existing.
        rm = paths.results_manager
        rm.set_named_results(results=rs)

        # get the results by paths name
        some = rm.get_named_results(pathsname)
        assert some
        assert len(some) == 1

        # create new results for new file
        filename = "drink"
        more_result = Result(
            lines=[],
            csvpath=path,
            file_name=filename,
            paths_name=pathsname,
            run_index=1,
            run_time=None,
            run_dir=run_dir,
        )
        rm.add_named_result(more_result)

        #
        # get results by paths name. same paths, different file, so 2
        many = rm.get_named_results(pathsname)
        assert many
        assert len(many) == 2
        assert rm.get_number_of_results(pathsname) == 2

        # remove paths
        rm.remove_named_results(pathsname)

        assert len(rm.named_results) == 0

    def test_results_print_to_printouts(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.file_manager.add_named_files_from_dir(
            f"tests{os.sep}test_resources{os.sep}named_files"
        )
        paths.paths_manager.add_named_paths(
            name="print_test",
            paths=[
                """$[3][
                        print("my msg", "error")
                        print("my other msg", "foo-bar")
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
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.file_manager.add_named_files_from_dir(
            f"tests{os.sep}test_resources{os.sep}named_files"
        )
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
        # should not blow up because we stringify error
        assert results
