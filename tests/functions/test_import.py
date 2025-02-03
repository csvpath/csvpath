import unittest
import pytest
import os
from csvpath.matching.productions import Term, Equality, Header
from csvpath import CsvPath, CsvPaths
from csvpath.util.config import OnError
from csvpath.matching.util.exceptions import MatchException
from csvpath.util.exceptions import CsvPathsException

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"


class TestFunctionsImport(unittest.TestCase):
    def test_function_import1(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = [OnError.RAISE.value]
        # import has no name
        with pytest.raises(MatchException):
            path.parse(f" ${PATH}[*] [ import() ] ")
            path.fast_forward()
        # no csvpaths
        with pytest.raises(MatchException):
            path.parse(f""" ${PATH}[*] [ import("test") ] """)
            path.fast_forward()

    def test_function_import2(self):
        paths = CsvPaths()
        paths.config.csvpath_errors_policy = [OnError.RAISE.value]

        paths.file_manager.add_named_files_from_dir(
            f"tests{os.sep}test_resources{os.sep}named_files"
        )
        paths.paths_manager.add_named_paths_from_dir(
            directory=f"tests{os.sep}test_resources{os.sep}named_paths"
        )
        # food has 3 match components so we'll have 5 total after import
        paths.collect_paths(filename="food", pathsname="food")
        path = paths.csvpath()
        path.config.csvpaths_errors_policy = [OnError.RAISE.value]
        path.parse(f""" ${PATH}[*] [ import("food") yes() ] """)
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
        paths = CsvPaths()
        paths.config.csvpath_errors_policy = [OnError.RAISE.value]
        paths.config.csvpaths_errors_policy = [OnError.RAISE.value]

        paths.file_manager.add_named_file(name="test", path=PATH)
        paths.paths_manager.add_named_paths_from_file(
            name="paths",
            file_path=f"tests{os.sep}test_resources{os.sep}named_paths{os.sep}import_internal.csvpath",
        )

        paths.collect_paths(filename="test", pathsname="paths")
        pvars = paths.results_manager.get_variables("paths")
        assert "hey" in pvars
        results = paths.results_manager.get_named_results("paths")
        assert len(results) == 2
        print(f"test_imports_function_3: {results}")
        if results[0].csvpath.identity == "importer":
            importer = results[0]
            importable = results[1]
        else:
            importer = results[1]
            importable = results[0]

        print(f"test_imports_function_3: importable: {importable}")
        assert len(importable) == 0
        assert importable.csvpath.will_run is False

        assert len(importer) == 9
        assert importer.csvpath.will_run is True
