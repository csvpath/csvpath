import unittest
import os
from datetime import datetime
from csvpath.managers.registrar import Registrar
from csvpath import CsvPaths
from csvpath.util.config import Config


class TestListeners(unittest.TestCase):
    def test_additional_listeners1(self):
        stmt = "from csvpath.managers.run.run_listener_stdout import StdOutRunListener"
        r = Registrar(csvpaths=CsvPaths())
        listeners = [r]
        assert len(listeners) == 1
        r.load_additional_listener(stmt, listeners)
        assert len(listeners) == 2

    def test_additional_listeners3(self):
        testini = f"tests{os.sep}test_resources{os.sep}deleteme{os.sep}config.ini"
        if os.path.exists(testini):
            os.remove(testini)
        os.environ[Config.CSVPATH_CONFIG_FILE_ENV] = testini
        paths = CsvPaths()
        config = paths.config
        assert os.path.exists(testini)
        os.environ[Config.CSVPATH_CONFIG_FILE_ENV] = f"config{os.sep}config.ini"
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
        # assert "b" in listeners

        r = Registrar(paths)
        # assert len(r.listeners) == 1
        listeners = [r]
        r.load_additional_listeners("file", listeners)
        assert len(listeners) == 3
