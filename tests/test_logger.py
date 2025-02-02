import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.matcher import Matcher
from csvpath.util.log_utility import LogUtility, LogException


class TestLogger(unittest.TestCase):
    def test_logger_wrong_log_level(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["raise"]
        config = path.config
        config.csvpath_log_level = "noway"
        with pytest.raises(LogException):
            LogUtility.logger(path)

    def test_logger_wrong_component(self):
        matcher = Matcher(csvpath=None, data="[]", headers=[])
        with pytest.raises(LogException):
            LogUtility.logger(matcher, "error")

        with pytest.raises(LogException):
            LogUtility.logger(None, "error")

    def test_logger_brief_stack_trace(self):
        path = CsvPath()
        string = LogUtility.log_brief_trace(logger=path.logger)
        assert string.find(f"{os.sep}util{os.sep}log_utility.py") > -1
