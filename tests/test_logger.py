import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.matcher import Matcher
from csvpath.util.log_utility import LogUtility, LogException


class TestLogger(unittest.TestCase):
    def test_logger_wrong_log_level(self):
        path = CsvPath()
        with pytest.raises(LogException):
            LogUtility.logger(path, "noway")

    def test_logger_wrong_component(self):
        matcher = Matcher(csvpath=None, data="[]", headers=[])
        with pytest.raises(LogException):
            LogUtility.logger(matcher, "noway")
