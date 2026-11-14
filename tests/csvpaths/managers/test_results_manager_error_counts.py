import os
import unittest
from csvpath import CsvPaths

FILE = os.path.join("tests", "csvpaths", "test_resources", "test.csv")
NAME = "results_manager_error_counts"


class TestResultsManagerErrorCounts(unittest.TestCase):
    def test_number_of_errors_sums_each_result(self):
        #
        # get_number_of_errors() called r.errors_count(), but errors_count is
        # a property, so it always raised TypeError: 'int' object is not callable
        #
        paths = CsvPaths()
        paths.file_manager.add_named_file(name=NAME, path=FILE)
        paths.paths_manager.add_named_paths(
            name=NAME,
            paths=[
                #
                # add() rejects a non-numeric header value on each of the 9
                # lines. collect the errors and keep going.
                #
                "~ id: bad validation-mode: collect, no-raise, no-stop ~ $[*][ @x = add(#firstname, 1) ]",
                "~ id: ok ~ $[*][ @y = count() ]",
            ],
        )
        paths.collect_paths(filename=NAME, pathsname=NAME)
        results = paths.results_manager.get_named_results(NAME)
        counts = {r.csvpath.identity: r.errors_count for r in results}
        assert counts == {"bad": 9, "ok": 0}
        n = paths.results_manager.get_number_of_errors(NAME)
        assert isinstance(n, int)
        assert n == 9
        assert paths.results_manager.has_errors(NAME) is True
