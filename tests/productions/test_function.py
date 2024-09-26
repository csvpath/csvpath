import unittest
import pytest
from csvpath.matching.functions.function_factory import (
    FunctionFactory,
    InvalidNameException,
)
from csvpath.matching.functions.counting.count import Count
from csvpath.matching.functions.function import Function
from csvpath.csvpath import CsvPath


class TestFunction(unittest.TestCase):
    def test_bad_name(self):
        count = Count(None, name="count")
        with pytest.raises(InvalidNameException):
            FunctionFactory.add_function(name=None, function=count)
        with pytest.raises(InvalidNameException):
            FunctionFactory.add_function(name=1, function=count)
        with pytest.raises(InvalidNameException):
            FunctionFactory.add_function(name="", function=count)
        with pytest.raises(InvalidNameException):
            FunctionFactory.add_function(name="A123", function=count)
        with pytest.raises(InvalidNameException):
            FunctionFactory.add_function(name="count", function=count)

        c = CsvPath()
        c.parse("$tests/test_resources/test.csv[*][yes()]")
        c.fast_forward()
        FunctionFactory.add_function("iamaname", count)
        f = FunctionFactory.get_function(matcher=c.matcher, name="iamaname")
        assert f is not None
        assert isinstance(f, Function)
