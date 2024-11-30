import unittest
from datetime import datetime
from csvpath.managers.registrar import Registrar
from csvpath import CsvPaths


class TestListeners(unittest.TestCase):
    def test_additional_listeners1(self):
        stmt = "from csvpath.managers.run.stdout_run_listener import StdOutRunListener"
        r = Registrar(None)
        assert len(r.listeners) == 1
        r.load_additional_listener(stmt)
        assert len(r.listeners) == 2

    def test_additional_listeners2(self):
        csvpaths = CsvPaths()
        config = csvpaths.config
        config._additional_listeners = {}
        config._additional_listeners["run"] = [
            "from csvpath.managers.run.stdout_run_listener import StdOutRunListener",
            "from csvpath.managers.run.stdout_run_listener import StdOutRunListener",
        ]
        r = Registrar(csvpaths)
        assert len(r.listeners) == 1
        r.load_additional_listeners("run")
        assert len(r.listeners) == 3
