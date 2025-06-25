import unittest
import pytest
import logging
import os
from io import StringIO as buffer
from csvpath import CsvPath
from csvpath.util.log_utility import LogUtility

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsDebug(unittest.TestCase):
    def test_function_log1(self):
        buf = buffer()
        h = logging.StreamHandler(buf)
        path = CsvPath()
        logger = LogUtility.logger(path, "info")
        path.logger = logger
        path.logger.addHandler(h)
        path.parse(
            f"""
            ${PATH}[1]
            [ log( "fish")
                log("rats", "rodents")
            ]"""
        )
        path.collect()
        path.logger.removeHandler(h)
        text = buf.getvalue()
        buf.close()
        assert text.find("fish") > -1
        assert text.find("rats") > -1

    def test_function_log2(self):
        buf = buffer()
        h = logging.StreamHandler(buf)
        path = CsvPath()
        logger = LogUtility.logger(path, "info")
        path.logger = logger
        path.logger.addHandler(h)
        path.parse(
            f"""
            ${PATH}[1]
            [ log("fish", "debug") ]"""
        )
        path.collect()
        path.logger.removeHandler(h)
        text = buf.getvalue()
        buf.close()
        assert text.find("fish") == -1

    def test_function_log3(self):
        buf = buffer()
        h = logging.StreamHandler(buf)
        path = CsvPath()
        logger = LogUtility.logger(path, "warning")
        path.logger = logger
        path.logger.addHandler(h)
        path.parse(
            f"""
            ${PATH}[1]
            [ log("molluscs", "warning") ]"""
        )
        path.collect()
        path.logger.removeHandler(h)
        text = buf.getvalue()
        buf.close()
        assert text.find("molluscs") > -1

    def test_function_log4(self):
        buf = buffer()
        h = logging.StreamHandler(buf)
        path = CsvPath()
        logger = LogUtility.logger(path, "error")
        path.logger = logger
        path.logger.addHandler(h)
        path.parse(
            f"""
            ${PATH}[1]
            [ log("butterflies", "error") ]"""
        )
        path.collect()
        path.logger.removeHandler(h)
        text = buf.getvalue()
        buf.close()
        assert text.find("butterflies") > -1

    def test_function_debug(self):
        path = CsvPath()
        path.logger.level = logging.DEBUG
        assert path.logger.level == logging.DEBUG
        if path.logger.level == logging.DEBUG:
            path.logger.level = logging.INFO
        assert path.logger.level != logging.DEBUG
        path.parse(
            f"""
            ${PATH}[1]
            [ debug( "error") ]"""
        )
        path.collect()
        assert path.logger.level == logging.ERROR

    def test_function_debug_2(self):
        # debug was not returning default match and so was
        # blocking matches, which as a side-effect it should
        # not do.
        path = CsvPath()
        lines = path.collect(
            f"""
            ${PATH}[*]
            [ debug( "error") ]"""
        )
        assert len(lines) == 9

    def test_function_brief_stack_trace(self):
        path = CsvPath()
        path.logger.level = logging.DEBUG
        assert path.logger.level == logging.DEBUG
        if path.logger.level == logging.DEBUG:
            path.logger.level = logging.INFO
        assert path.logger.level != logging.DEBUG
        path.parse(
            f"""
            ${PATH}[1]
            [ brief_stack_trace() ]"""
        )
        path.collect()
        assert path.last_line
        assert path.last_line.find(", line") > -1
        path = CsvPath().parse(
            f"""
            ${PATH}[1]
            [ brief_stack_trace("print") ]"""
        )
        path.collect()
        assert path.last_line.find(", line") > -1

    def test_function_do_when_stack(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [
                yes() -> print("") no() -> print("") no() -> print("")
                @dw = do_when_stack()
            ]
        """
        )
        path.collect()
        assert path.variables["dw"] == [True, False, False]
