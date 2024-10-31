import unittest
import pytest
from csvpath.matching.productions import Term, Equality, Header

from csvpath import CsvPath, CsvPaths
from csvpath.util.error import OnError
from csvpath.matching.util.exceptions import MatchException
from csvpath.util.exceptions import CsvPathsException
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsImport(unittest.TestCase):
    def test_function_import1(self):
        path = CsvPath()
        Save._save(path, "test_function_import")

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

        paths.file_manager.add_named_files_from_dir("tests/test_resources/named_files")
        paths.paths_manager.add_named_paths_from_dir(
            directory="tests/test_resources/named_paths"
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

        paths.file_manager.add_named_file(name="test", path=PATH)
        paths.paths_manager.add_named_paths_from_file(
            name="paths",
            file_path="tests/test_resources/named_paths/import_internal.csvpath",
        )

        paths.collect_paths(filename="test", pathsname="paths")
        pvars = paths.results_manager.get_variables("paths")
        assert "hey" in pvars
        results = paths.results_manager.get_named_results("paths")
        assert len(results) == 2
        if results[0].csvpath.identity == "importer":
            importer = results[0]
            importable = results[1]
        else:
            importer = results[1]
            importable = results[0]

        print(f"importable: {importable.csvpath}")
        assert len(importable) == 0
        assert importable.csvpath.run_mode is False

        print(f"importer: {importer.csvpath}")
        assert len(importer) == 9
        assert importer.csvpath.run_mode is True
