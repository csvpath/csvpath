import unittest
import os
from datetime import datetime
from csvpath.managers.registrar import Registrar
from csvpath import CsvPaths
from csvpath.util.config import Config


class TestListeners(unittest.TestCase):
    def test_additional_listeners1(self):
        r = Registrar(csvpaths=CsvPaths())
        assert r.listeners is None
        r.load_additional_listeners_if()
        assert len(r.listeners) == 1

    def test_additional_listeners3(self):
        testini = "tests/test_resources/deleteme/config.ini"
        if os.path.exists(testini):
            os.remove(testini)
        os.environ[Config.CSVPATH_CONFIG_FILE_ENV] = testini
        paths = CsvPaths()
        config = paths.config
        assert os.path.exists(testini)
        os.environ[Config.CSVPATH_CONFIG_FILE_ENV] = "config/config.ini"
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
        r.type = "file"
        r.load_additional_listeners_if()
        assert len(r.listeners) == 3
