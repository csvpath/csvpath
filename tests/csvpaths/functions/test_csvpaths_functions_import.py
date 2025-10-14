import unittest
import pytest
import os
from csvpath.matching.productions import Term, Equality, Header
from csvpath import CsvPaths
from csvpath.util.config import OnError
from csvpath.matching.util.exceptions import MatchException
from csvpath.util.exceptions import CsvPathsException
from tests.csvpaths.builder import Builder

FILE = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}test.csv"
PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths{os.sep}import_internal.csvpath"

PATHS_DIR = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_paths"
FILES_DIR = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}named_files"


class TestCsvPathsFunctionsImport(unittest.TestCase):
    def test_function_import2(self):
        paths = Builder().build()

        paths.file_manager.add_named_files_from_dir(FILES_DIR)
        paths.paths_manager.add_named_paths_from_dir(directory=PATHS_DIR)
        # food has 3 match components so we'll have 5 total after import
        paths.collect_paths(filename="food", pathsname="food")
        path = paths.csvpath()
        path.config.csvpaths_errors_policy = [OnError.RAISE.value]
        path.parse(f""" ${FILE}[*] [ import("food") yes() ] """)
        path.fast_forward()
        #
        # let's check order and matcher
        #
        es = path.matcher.expressions
        assert len(es) == 5
        assert es[0][0].matcher == path.matcher
        assert isinstance(es[0][0].children[0], Equality)
        assert isinstance(es[0][0].children[0].children[0], Equality)
        assert isinstance(es[0][0].children[0].children[0].children[0], Header)
        assert es[0][0].children[0].children[0].children[0].name == "type"
        assert es[0][0].children[0].children[0].children[0].matcher == path.matcher
        #
        # check original stuff is still in the correct place
        #
        assert es[3][0].matcher == path.matcher
        assert es[3][0].children[0].name == "import"
        assert es[3][0].children[0].matcher == path.matcher

    def test_function_import3(self):
        paths = Builder().build()
        paths.config.csvpath_errors_policy = [OnError.RAISE.value]
        paths.config.csvpaths_errors_policy = [OnError.RAISE.value]

        paths.file_manager.add_named_file(name="test", path=FILE)
        paths.paths_manager.add_named_paths_from_file(name="paths", file_path=PATH)

        ref = paths.collect_paths(filename="test", pathsname="paths")
        pvars = paths.results_manager.get_variables("paths")

        assert "hey" in pvars
        results = paths.results_manager.get_named_results("paths")
        #
        # when we do run-mode:no-run there are no results
        #
        assert len(results) == 1
        assert results[0].csvpath.identity == "importer"
        assert len(results[0]) == 9
        assert results[0].csvpath.will_run is True
