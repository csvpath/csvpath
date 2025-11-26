from lxml.etree import XPathEvalError
import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException


PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsXPath(unittest.TestCase):
    def test_function_xpath1(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise, print ~
            ${PATH}[*][
                @s = xpath("<xml><is>great</is></xml>", "/xml/is")
            ]"""
        )
        path.fast_forward()
        assert "s" in path.variables
        assert path.variables["s"] == "great"

    def test_function_xpath2(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise, print ~
            ${PATH}[*][
                @s = xpath("<xml><is><great degree='ish'/></is></xml>", "/xml/is/great/@degree")
            ]"""
        )
        path.fast_forward()
        assert "s" in path.variables
        assert path.variables["s"] == "ish"

    def test_function_xpath3(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise, print ~
            ${PATH}[*][
                @s = xpath("<xml><is><great degree='ish'/></is></xml>", "")
            ]"""
        )
        with pytest.raises(XPathEvalError):
            path.fast_forward()

    def test_function_xpath4(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise, print ~
            ${PATH}[*][
                @s = xpath("", "/xml/is/great/@degree")
            ]"""
        )
        #
        # should pass, not raise exception
        #
        path.fast_forward()

    def test_function_xpath5(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise, print ~
            ${PATH}[*][
                @s = xpath(none(), "/xml/is/great/@degree")
            ]"""
        )
        #
        # should pass, not raise exception
        #
        path.fast_forward()
