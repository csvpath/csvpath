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
        scanner = path.parse(f'${PATH}[*][count(#0="David")=1]')

        for i, ln in enumerate(path.next()):
            print(f"\n\n\n>>>>>>>>>>>>>>>>>>>>>> {i} = {ln}")
            assert i == 1


