import unittest
import pytest
import logging
from io import StringIO as buffer
from csvpath import CsvPath
from csvpath.matching.util.exceptions import ChildrenException
from tests.save import Save
from csvpath.util.log_utility import LogUtility

PATH = "tests/test_resources/test.csv"


class TestFunctionsDebug(unittest.TestCase):
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
        Save._save(path, "test_function_debug")
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

    def test_function_brief_stack_trace(self):
        path = CsvPath()
        Save._save(path, "test_function_brief_stack_trace")
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
        Save._save(path, "test_function_do_when_stack")
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
        print(f"test_function_do_when_stack: path.vars: {path.variables}")
        assert path.variables["dw"] == [True, False, False]
