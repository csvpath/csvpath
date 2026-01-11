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
NAME = "foodzz"


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

    def test_csvpaths_return_file_ref(self):
        #
        # tests if the file reference returned by add_named_file is
        # stored in the two file manifests
        #
        paths = CsvPaths()
        if paths.file_manager.get_named_file(NAME) is not None:
            paths.file_manager.remove_named_file(NAME)
        assert paths.file_manager.get_named_file(NAME) is None
        ref = paths.file_manager.add_named_file(name=NAME, path=PATH)
        assert paths.file_manager.get_named_file(NAME) is not None
        assert ref is not None
        assert ref.startswith(f"${NAME}.files.")
        #
        # check the overall mani
        #
        mani = paths.file_manager.get_manifest(ref)
        assert mani is not None
        assert "reference" in mani[len(mani) - 1]
        assert mani[len(mani) - 1]["reference"] == ref
        #
        # check named-file's mani
        #
        reg = paths.file_manager.registrar
        home = paths.file_manager.named_file_home(NAME)
        p = reg.manifest_path(home)
        mani = reg.get_manifest(p)
        assert mani is not None
        assert "reference" in mani[len(mani) - 1]
        assert mani[len(mani) - 1]["reference"] == ref

        paths.file_manager.remove_named_file(NAME)
        assert paths.file_manager.get_named_file(NAME) is None

        """
        cnt = 0
        for line in paths.next_paths(filename="food", pathsname="food"):
            cnt += 1
        assert cnt == 1
        results = paths.results_manager.get_named_results("food")
        paths = None
        assert results
        assert len(results) == 1
        result = results[0]
        path = result.csvpath
        len(result) == 1
        v = path.variables
        assert v
        assert "candy" in v
        #
        # reload
        #
        paths = CsvPaths()
        results = paths.results_manager.get_named_results("food")
        assert results
        assert len(results) == 1
        result = results[0]
        path = result.csvpath
        len(result) == 1
        v = path.variables
        assert v
        assert "candy" in v
        """
