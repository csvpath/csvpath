import unittest
from csvpath import CsvPaths
from csvpath.util.line_spooler import LineSpooler
from csvpath.managers.results.readers.readers import ResultReadersFacade


class TestResultReaders(unittest.TestCase):
    def test_result_readers(self):
        f = ResultReadersFacade(None)
        # f.run_dir = "testing!"
        # f.identity = "still-testing!"
        f.load_readers()
        assert f.errors_reader
        assert f.unmatched_reader
        assert f.printouts_reader
        assert f.lines_reader

    def test_result_file_lines_reader(self):
        paths = CsvPaths()
        paths.file_manager.add_named_file(
            name="food", path="tests/test_resources/named_files/food.csv"
        )
        paths.paths_manager.add_named_paths(
            name="food", from_file="tests/test_resources/named_paths/food.csvpaths"
        )
        paths.collect_paths(pathsname="food", filename="food")
        results = paths.results_manager.get_named_results("food")
        assert len(results) == 2
        result = results[0]
        lines = result.lines
        assert lines
        assert isinstance(lines, LineSpooler)
        #
        # now ready to reload
        #
        readers = ResultReadersFacade(result)
        assert readers.instance_dir
        lines2 = readers.lines
        assert lines2 is not None
        assert len(lines2) == 1
        assert len(lines) == len(lines2)

    def test_reload_errors(self):
        paths = CsvPaths()
        paths.file_manager.add_named_file(
            name="test", path="tests/test_resources/test.csv"
        )
        paths.paths_manager.add_named_paths(
            name="error_reload",
            from_file="tests/test_resources/named_paths/error_reload.csvpath",
        )
        paths.collect_paths(pathsname="error_reload", filename="test")
        results = paths.results_manager.get_named_results("error_reload")
        assert results is not None
        assert len(results) == 1
        errors = results[0].errors
        assert errors
        assert len(errors) == 8

        paths = CsvPaths()
        results = paths.results_manager.get_named_results("error_reload")
        assert results is not None
        assert len(results) == 1
        errors2 = results[0].errors
        assert errors2 is not None
        assert len(errors2) == len(errors)

        assert errors[0] == errors2[0]

    def test_reload_printouts(self):
        print("")
        paths = CsvPaths()
        paths.file_manager.add_named_file(
            name="people", path="tests/test_resources/test.csv"
        )
        paths.paths_manager.add_named_paths(
            name="arrivals",
            from_file="tests/test_resources/named_paths/people.csvpaths",
        )
        paths.collect_paths(pathsname="arrivals", filename="test")
        results = paths.results_manager.get_named_results("arrivals")
        assert results is not None
        assert len(results) == 2
        print("RESULTS ONE")
        print(" >> name tags")
        printouts = results[0].get_printouts("name tags")
        for p in printouts:
            print(f"  ... {p}")
        assert printouts
        assert len(printouts) == 7

        print(">> checklist")
        printouts = results[0].get_printouts("checklist")
        for p in printouts:
            print(f"  ... {p}")
        # assert printouts
        # assert len(printouts) == 8
        #
        #
        #
        paths = CsvPaths()
        results2 = paths.results_manager.get_named_results("arrivals")
        assert results2 is not None
        assert len(results2) == 2

        print("\nRESULTS TWO")
        print(" >> name tags")
        printouts = results2[0].get_printouts("name tags")
        for p in printouts:
            print(f"  ... {p}")
        assert printouts
        assert len(printouts) == 7

        print(" >> remarks")
        printouts = results2[1].get_printouts("remarks")
        for p in printouts:
            print(f"  ... {p}")
        assert printouts
        assert len(printouts) == 3


######
#
# lines
# unmatched
#
