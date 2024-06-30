import unittest
from csvpath.matching.matcher import Matcher
from csvpath.matching.functions.count import Count
from csvpath.matching.functions.function_factory import FunctionFactory
from csvpath.csvpath import CsvPath

PATH = "tests/test_resources/test.csv"

class TestFunctions(unittest.TestCase):

#============= count ================

    def test_function_factory(self):
        count = FunctionFactory.get_function(None, name="count", child=None)
        assert count

    def test_function_count_empty(self):
        f = FunctionFactory.get_function(None, name="count", child=None)
        assert f.to_value() == 0 # no matcher or csvpath == -1 + eager match 1


    def test_function_count_equality(self):
        path = CsvPath()
        scanner = path.parse(f'${PATH}[*][count(#lastname="Bat")=7]')
        lines = path.collect()
        print(f"test_function_count_equality: lines: {lines}")
        assert len(lines) == 1
        assert lines[0][0] == "Frog"

    def test_function_length(self):
        path = CsvPath()
        scanner = path.parse(f'${PATH}[*][length(#lastname)=3]')
        lines = path.collect()
        print(f"test_function_length: lines: {len(lines)}")
        assert len(lines) == 7

    def test_function_not(self):
        path = CsvPath()
        scanner = path.parse(f'${PATH}[*][not(length(#lastname)=3)]')
        lines = path.collect()
        print(f"test_function_not: lines: {len(lines)}")
        assert len(lines) == 2

    def test_function_now(self):
        path = CsvPath()
        # obviously this will break and need updating 1x a year
        scanner = path.parse(f'${PATH}[*][now("%Y") = "2024"]')
        lines = path.collect()
        print(f"test_function_now: lines: {len(lines)}")
        assert len(lines) == 9

    def test_function_in(self):
        path = CsvPath()
        scanner = path.parse(f'${PATH}[*][in( #0 , "Bug|Bird|Ants" )]')
        lines = path.collect()
        print(f"test_function_in: lines: {len(lines)}")
        assert len(lines) == 3

    def test_function_concat(self):
        path = CsvPath()
        scanner = path.parse(f'${PATH}[*][ #0 = concat("B" , "ird") ]')
        lines = path.collect()
        print(f"test_function_concat: lines: {len(lines)}")
        assert len(lines) == 1


