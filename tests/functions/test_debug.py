import unittest
import pytest
import logging
from csvpath import CsvPath
from csvpath.matching.util.exceptions import ChildrenException
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsDebug(unittest.TestCase):
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
        print(f"brief stack trace: {path.printers[0].last_line}")
        assert path.last_line
        assert path.last_line.find(", line") > -1
