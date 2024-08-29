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

        rm = paths.results_manager
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
        rm = paths.results_manager
        rm.set_named_results(results=rs)

        # get the results by paths name
        some = rm.get_named_results(pathsname)
        assert some
        assert len(some) == 1

        # create new results for new file
        filename = "drink"
        more_result = CsvPathResult(
            lines=[], csvpath=path, file_name=filename, paths_name=pathsname
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
