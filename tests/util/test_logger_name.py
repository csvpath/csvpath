import unittest
from csvpath import CsvPath, CsvPaths
from csvpath.util.log_utility import LogUtility as lout


class TestLoggerName(unittest.TestCase):
    def test_util_logger_name(self):
        path = CsvPath(project="xyz", project_context="pdq")
        assert path.logger.name.find("xyz") > -1
        assert path.logger.name.find("pdq") > -1

        path = CsvPath()
        assert path.logger.name.find("no_project_context") > -1
        assert path.logger.name.find("no_project_name") > -1

        paths = CsvPaths(project="xyz", project_context="pdq")
        path = paths.csvpath()
        assert path.logger.name.find("xyz") > -1
        assert path.logger.name.find("pdq") > -1
