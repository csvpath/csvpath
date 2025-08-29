import unittest
import os
from csvpath import CsvPaths
from csvpath.util.path_util import PathUtility as pathu
from tests.csvpaths.builder import Builder

from csvpath.util.references.results_reference_finder_2 import (
    ResultsReferenceFinder2 as ResultsReferenceFinder,
)
from csvpath.util.references.files_reference_finder_2 import (
    FilesReferenceFinder2 as FilesReferenceFinder,
)


PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}test.csv"
PATHS = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}food.csvpaths"


class TestCsvPathsAbsoluteRef(unittest.TestCase):
    def test_abs_ref_return_1(self):
        paths = Builder().build()
        paths.config.add_to_config("errors", "csvpath", "raise, collect, print")
        name = "absrefmkr"

        paths.paths_manager.remove_named_paths(name)
        assert not paths.paths_manager.has_named_paths(name)

        paths.results_manager.remove_named_results(name)
        assert not paths.results_manager.has_named_results(name)

        pathsref = paths.paths_manager.add_named_paths_from_file(
            name=name, file_path=PATHS
        )
        assert pathsref
        assert pathsref == f"${name}.csvpaths.0:from"
        lst = paths.paths_manager.get_named_paths(name)
        assert lst
        assert len(lst) == 2

        fileref = paths.file_manager.add_named_file(name="food", path=PATH)
        assert fileref
        results = FilesReferenceFinder(paths, reference=fileref).query()
        assert results.files
        assert len(results.files) == 1
        assert paths.file_manager.has_named_file(fileref)

        runref = paths.collect_paths(pathsname=name, filename="food")
        assert runref is not None
        assert runref.startswith("$")
        results = ResultsReferenceFinder(paths, reference=runref).query()
        assert results.files
        assert len(results.files) == 1
        assert paths.results_manager.has_named_results(runref)
