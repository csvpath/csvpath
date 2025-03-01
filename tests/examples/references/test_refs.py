import unittest
import os
from csvpath import CsvPaths
from csvpath.util.file_readers import DataFileReader


class TestRefs(unittest.TestCase):
    def test_rewind(self):
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.file_manager.add_named_file(
            name="people",
            path=f"tests{os.sep}examples{os.sep}references{os.sep}assets{os.sep}people.csv",
        )
        paths.paths_manager.add_named_paths_from_file(
            name="sourcemode",
            file_path=f"tests{os.sep}examples{os.sep}references{os.sep}assets{os.sep}sourcemode.csvpaths",
        )
        paths.collect_paths(filename="people", pathsname="sourcemode")
        results = paths.results_manager.get_named_results("sourcemode")
        assert len(results) == 3
        #
        # do the refs
        #
        paths = CsvPaths()
        paths.add_to_config("errors", "csvpath", "raise, collect, print")
        paths.add_to_config("errors", "csvpaths", "raise, collect, print")
        paths.paths_manager.add_named_paths_from_file(
            name="sourcemode",
            file_path=f"tests{os.sep}examples{os.sep}references{os.sep}assets{os.sep}sourcemode2.csvpaths",
        )
        paths.collect_paths(
            filename="$sourcemode.results.202:last.source1",
            pathsname="$sourcemode.csvpaths.source2:from",
        )
        results = paths.results_manager.get_named_results("sourcemode")
        assert len(results) == 2
        assert results[1].csvpath.identity == "source3"
        #
        # the headers didn't change internally, we do the changes at each line
        #
        assert results[1].csvpath.headers == [
            "firstname",
            "lastname",
            "thinking",
            "count",
        ]
        for line in DataFileReader(
            results[1].data_file_path,
            filetype="csv",
            delimiter=results[1].csvpath.delimiter,
            quotechar=results[1].csvpath.quotechar,
        ).next():
            assert line == ["firstname", "lastname", "thinking"]
            break
