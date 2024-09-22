import unittest
import pytest
from csvpath.matching.productions import Term, Equality, Header

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
