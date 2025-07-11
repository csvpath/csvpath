import unittest
import os
from datetime import datetime
from csvpath.managers.registrar import Registrar
from csvpath import CsvPaths
from csvpath.util.config import Config
from tests.csvpaths.builder import Builder
from csvpath.util.path_util import PathUtility as pathu

TINI = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}deleteme{os.sep}config.ini"


class TestCsvPathsManagersListeners(unittest.TestCase):
    def test_additional_listeners1(self):
        stmt = "from csvpath.managers.run.run_listener_stdout import StdOutRunListener"
        paths = Builder().build()
        r = Registrar(csvpaths=paths)
        listeners = [r]
        assert len(listeners) == 1
        r.load_additional_listener(stmt, listeners)
        assert len(listeners) == 2

    def test_additional_listeners3(self):
        paths = Builder().build()
        config = paths.config
        config.add_to_config("listeners", "groups", "foo, bar, baz")
        config.add_to_config(
            "listeners",
            "foo.file",
            "from csvpath.managers.run.run_listener_stdout import StdOutRunListener",
        )
        config.add_to_config(
            "listeners",
            "bar.file",
            "from csvpath.managers.run.run_listener_stdout import StdOutRunListener",
        )
        listeners = config.additional_listeners("file")
        assert len(listeners) == 2
        assert (
            "from csvpath.managers.run.run_listener_stdout import StdOutRunListener"
            in listeners
        )
        r = Registrar(paths)
        listeners = [r]
        r.load_additional_listeners("file", listeners)
        assert len(listeners) == 3
