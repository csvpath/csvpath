import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException


PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.jsonl"
DOC = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}jsondoc-sm.jsonl"


class TestCsvPathFunctionsJSONPath(unittest.TestCase):
    def test_function_jsonpath1(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise, print ~
            ${PATH}[8][
                @s = jsonpath(#2, "$[*]")
            ]"""
        )
        path.fast_forward()
        assert "s" in path.variables
        s = path.variables["s"]
        assert len(s) == 2

    def test_function_jsonpath2(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:print, raise ~
            ${DOC}[1][ @s = jsonpath(#0, "$.[0]") ]"""
        )
        path.fast_forward()
        assert "s" in path.variables
        s = path.variables["s"]
        assert s
        assert s == "a"
