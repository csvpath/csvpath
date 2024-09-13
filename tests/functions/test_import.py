import unittest
import pytest
from csvpath import CsvPath, CsvPaths
from csvpath.util.error import OnError
from csvpath.matching.util.exceptions import MatchComponentException, ChildrenException
from csvpath.util.exceptions import CsvPathsException
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsImport(unittest.TestCase):
    def test_function_import1(self):
        path = CsvPath()
        Save._save(path, "test_function_import")

        path.config.csvpath_errors_policy = [OnError.RAISE.value]
        # import has no name
        with pytest.raises(ChildrenException):
            path.parse(f" ${PATH}[*] [ import() ] ")
        # no csvpaths
        with pytest.raises(MatchComponentException):
            path.parse(f""" ${PATH}[*] [ import("test") ] """)

    def test_function_import2(self):
        paths = CsvPaths()
        paths.config.csvpath_errors_policy = [OnError.RAISE.value]

        paths.files_manager.add_named_files_from_dir("tests/test_resources/named_files")
        paths.paths_manager.add_named_paths_from_dir(
            directory="tests/test_resources/named_paths"
        )
        paths.collect_paths(filename="food", pathsname="food")

        path = paths.csvpath()
        path.config.csvpaths_errors_policy = [OnError.RAISE.value]
        path.parse(f""" ${PATH}[*] [ import("food") ] """)

        #
        # let's check if all our match components have the right matcher
        #
