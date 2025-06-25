import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.util.config import OnError
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsImport(unittest.TestCase):
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
