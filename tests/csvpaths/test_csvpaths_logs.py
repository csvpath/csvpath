import unittest
import os
import shutil
from csvpath import CsvPaths
from csvpath.util.line_monitor import LineMonitor
from csvpath.util.log_utility import LogUtility as lout
from csvpath.util.log_utility import LogUtility
from csvpath.util.nos import Nos

PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathsLogs(unittest.TestCase):
    def test_log_names_and_files(self):
        #
        # create a paths just to get and delete log files
        #
        paths = CsvPaths()
        path = paths.config.get(section="logging", name="log_file")
        parent = os.path.dirname(path)
        paths = None
        if Nos(path).exists():
            Nos(path).remove()
        #
        # new paths
        #
        paths = CsvPaths()
        logger = paths.logger
        for handler in logger.handlers:
            handler.flush()

        paths.file_manager.add_named_file(name="test", path=PATH)
        assert Nos(path).exists()
        assert paths.logger
        assert Nos(parent).exists()
        lst = Nos(parent).listdir()
        if ".DS_Store" in lst:
            lst.remove(".DS_Store")
        assert len(lst) == 1
        size = os.path.getsize(path)
        #
        # second values: new paths has different logger name, but
        # logs to the same log file
        #
        paths2 = CsvPaths(project_name="testing", project_context="abcdefg")
        paths2.file_manager.add_named_file(name="test", path=PATH)
        assert paths2.logger
        assert Nos(path).exists()
        assert Nos(parent).exists()

        lst = Nos(parent).listdir()
        if ".DS_Store" in lst:
            lst.remove(".DS_Store")
        assert len(lst) == 1
        size2 = os.path.getsize(path)
        assert size < size2
