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

        with pytest.raises(LogException):
            LogUtility.logger(None, "noway")

    def test_logger_brief_stack_trace(self):
        path = CsvPath()
        string = LogUtility.log_brief_trace(path.logger)
        print(f"test_logger_wrong_component: error trace: {string}")
        assert string.find("/util/log_utility.py") > -1
