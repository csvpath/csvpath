import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.scanning.scanner import Scanner
from csvpath.util.config import OnError

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathStopped(unittest.TestCase):
    def test_csvpath_stopped_1(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise, print")
        path.parse(f"""${PATH}[1*][yes()]""")
        path.fast_forward()
        assert not path.stopped

    def test_csvpath_stopped_2(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise, print")
        path.parse(f"""${PATH}[1-3][yes()]""")
        path.fast_forward()
        assert path.stopped

    def test_csvpath_stopped_3(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise, print")
        path.parse(
            f"""${PATH}[1*][
            line_number() == 3 -> stop()
        ]"""
        )
        path.fast_forward()
        assert path.stopped

    def test_csvpath_stopped_4(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "stop, print")
        path.parse(
            f"""
            ~ config says stop on error. we skip 0 and break on 3 leaving 2 matches. ~
            ${PATH}[1*][
                line_number.nocontrib() == 3 -> error("stop me!")
            ]
        """
        )
        lines = path.collect()
        assert len(lines) == 2
        assert path.stopped

    def test_csvpath_stopped_5(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "stop, print")
        path.parse(
            f"""
            ~
            config says stop, but validation mode says no-stop
            validation-mode:no-stop, no-raise, print
            ~
            ${PATH}[1*][
                line_number.nocontrib() == 3 -> error("stop me!")
            ]
        """
        )
        lines = path.collect()
        assert len(lines) == 7
        assert not path.stopped
