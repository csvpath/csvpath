import unittest
from csvpath import CsvPaths
from csvpath import ResultsManager, CsvPathResult


class TestResultsManager(unittest.TestCase):
    def test_results_mgr(self):
        print("")
        paths = CsvPaths()
        path = paths.csvpath()
        result = CsvPathResult(lines=[], path=path)
        results = [result]

        rs = {}
        rs["many"] = results

        rm = paths.results_manager
        rm.set_named_results(results=rs)

        some = rm.get_named_results("many")
        assert some
        assert len(some) == 1

        more_result = CsvPathResult(lines=[], path=path)

        rm.add_named_result("many", more_result)
        some = rm.get_named_results("many")
        assert some
        assert len(some) == 2

        rm.remove_named_results("many")
        assert len(rm.named_results) == 0
