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


