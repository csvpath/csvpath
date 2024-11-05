import unittest
from datetime import datetime
from csvpath import CsvPaths
from csvpath.managers.results_manager import ResultsManager
from csvpath.managers.result import Result
from csvpath.managers.result_serializer import ResultSerializer


class TestResultsManager(unittest.TestCase):
    def test_results_mgr1(self):
        print("")
        paths = CsvPaths()
        pathsname = "many"
        filename = "food"
        path = paths.csvpath()
        result = Result(
            lines=[],
            csvpath=path,
            file_name=filename,
            paths_name=pathsname,
            run_index=1,
            run_time=None,
        )
        results = [result]

        rs = {}
        rs[pathsname] = results

        rm = paths.results_manager
        rm.set_named_results(results=rs)

        some = rm.get_named_results(pathsname)
        assert some
        assert len(some) == 1

        more_result = Result(
            lines=[],
            csvpath=path,
            file_name=filename,
            paths_name=pathsname,
            run_index=1,
            run_time=None,
        )

        rm.add_named_result(more_result)
        some = rm.get_named_results(pathsname)
        assert some
        assert len(some) == 2

        rm.remove_named_results(pathsname)
        assert len(rm.named_results) == 0

    def test_results_mgr2(self):
        print("")
        # set up a csvpaths that will have 1 file and 1 set of paths
        filename = "food"
        pathsname = "many"
        paths = CsvPaths()
        # get a csvpath. the csvpaths is not 100% configured but we don't need it.
        path = paths.csvpath()
        # create a result as if we'd run paths against file
        result = Result(
            lines=[],
            csvpath=path,
            file_name=filename,
            paths_name=pathsname,
            run_index=1,
            run_time=None,
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

    def test_results_mgr3(self):
        paths = CsvPaths()
        paths.file_manager.add_named_files_from_dir("tests/test_resources/named_files")
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
        ps = results[0].get_printout_by_name("error")
        assert len(ps) == 1
        assert ps[0].find("my msg") > -1
        ps = results[0].get_printout_by_name("foo-bar")
        assert len(ps) == 1
        assert ps[0].find("my other msg") > -1

    def test_results_save_1(self):
        rs = ResultSerializer("tests/test_resources/serialized")
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
        )
