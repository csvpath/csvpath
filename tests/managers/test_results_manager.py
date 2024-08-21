import unittest
from csvpath import CsvPaths
from csvpath import ResultsManager, CsvPathResult


class TestResultsManager(unittest.TestCase):
    def test_results_mgr1(self):
        print("")
        paths = CsvPaths()
        pathsname = "many"
        filename = "food"
        path = paths.csvpath()
        result = CsvPathResult(
            lines=[], csvpath=path, file_name=filename, paths_name=pathsname
        )
        results = [result]

        rs = {}
        rs[pathsname] = results

        rm = paths.path_results_manager
        rm.set_named_results(results=rs)

        some = rm.get_named_results(pathsname)
        assert some
        assert len(some) == 1

        more_result = CsvPathResult(
            lines=[], csvpath=path, file_name=filename, paths_name=pathsname
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
        result = CsvPathResult(
            lines=[], csvpath=path, file_name=filename, paths_name=pathsname
        )
        results = [result]
        rs = {}
        rs[pathsname] = results

        # set the results in the paths results manager. this replaces any existing.
        prm = paths.path_results_manager
        prm.set_named_results(results=rs)
        # add the results to the file results manager. this doesn't replace anything
        frm = paths.file_results_manager
        frm.add_named_result(result)

        # get the results by paths name
        some = prm.get_named_results(pathsname)
        assert some
        assert len(some) == 1

        # get the results by filename
        food = frm.get_named_results(filename)
        assert food
        assert len(some) == 1
        # the results should be the same since the managers are just different
        # indexes to the same results.
        assert some == food
        # create new results for new file
        filename = "drink"
        more_result = CsvPathResult(
            lines=[], csvpath=path, file_name=filename, paths_name=pathsname
        )
        frm.add_named_result(more_result)
        prm.add_named_result(more_result)

        #
        # get results by path. this is a new pathname 'drink' so 1 result
        #
        some = frm.get_named_results(filename)
        assert some
        assert len(some) == 1
        assert frm.get_number_of_results(filename) == 1
        assert frm.get_number_of_results("food") == 1
        #
        # get results by paths name. same paths, different file, so 2
        many = prm.get_named_results(pathsname)
        assert many
        assert len(many) == 2
        assert prm.get_number_of_results(pathsname) == 2

        # remove paths
        # file no change
        prm.remove_named_results(pathsname)

        assert len(prm.named_results) == 0
        assert len(frm.named_results) == 2
        print(f"how many results on {filename}?")
        assert frm.get_number_of_results(filename) == 1
