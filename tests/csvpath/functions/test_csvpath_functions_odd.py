import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import ChildrenException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsOdd(unittest.TestCase):
    def test_function_oddeven_1(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise, print, stop")
        lines = path.parse(
            f"""~ validation-mode:raise, print ~
                ${PATH}[*] [
                    @l.nocontrib = odd( line_number() )
                    @m.nocontrib = eq( mod( line_number(), 2), 1)
                    not.nocontrib( @l == @m ) -> error("$.variable.l is not correct!")
                    print("Line $.csvpath.line_number is ($.variables.l/$.variables.m)")
                    @l == @m
                    ]"""
        ).collect()
        assert len(lines) == 9
        assert path.variables["l"] is False

    def test_function_oddeven_2(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise, print, stop")
        lines = path.parse(
            f"""~ validation-mode:raise, print ~
                ${PATH}[*] [
                    @l.nocontrib = even( line_number() )
                    @m.nocontrib = eq( mod( line_number(), 2), 0)
                    not.nocontrib( @l == @m ) -> error("$.variable.l is not correct!")
                    print("Line $.csvpath.line_number is ($.variables.l/$.variables.m)")
                    @l == @m
                    ]"""
        ).collect()
        assert len(lines) == 9
        assert path.variables["l"] is True
