import os
import unittest
import pytest
from csvpath.matching.functions.function_factory import (
    FunctionFactory,
    InvalidNameException,
)
from csvpath.matching.functions.counting.count import Count
from csvpath.matching.functions.function import Function
from csvpath.csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathProductionsFunction(unittest.TestCase):
    def test_bad_function_name_0(self):
        c = CsvPath()
        c.add_to_config("errors", "csvpath", "raise, collect, print")
        c.parse(f"${PATH}[*][yes()]")
        c.new_matcher(None)
        count = Count(matcher=c.matcher, name=None)
        #
        # functions must have names, either in the function or passed in with the
        # function.
        #
        with pytest.raises(InvalidNameException):
            FunctionFactory.add_function(name=None, function=count)

    def test_bad_function_name_1(self):
        c = CsvPath()
        c.add_to_config("errors", "csvpath", "raise, collect, print")
        c.parse(f"${PATH}[*][yes()]")
        c.new_matcher(None)
        count = Count(matcher=c.matcher, name="count..")
        #
        # we can have a function with a name  with a '.' and ending
        # with a '.' and two '.'s in a row
        #
        FunctionFactory.add_function(name=None, function=count)

    def test_bad_function_name_2(self):
        c = CsvPath()
        c.add_to_config("errors", "csvpath", "raise, collect, print")
        c.parse(f"${PATH}[*][yes()]")
        c.new_matcher(None)
        count = Count(matcher=c.matcher, name="count")
        with pytest.raises(InvalidNameException):
            FunctionFactory.add_function(name=1, function=count)

    def test_bad_function_name_3(self):
        c = CsvPath()
        c.add_to_config("errors", "csvpath", "raise, collect, print")
        c.parse(f"${PATH}[*][yes()]")
        c.new_matcher(None)
        count = Count(matcher=c.matcher, name="count")
        with pytest.raises(InvalidNameException):
            FunctionFactory.add_function(name="", function=count)

    def test_bad_name_4(self):
        #
        # we had not allowed numbers; however, the grammar always did and allowing
        # numbers makes sense.
        #
        c = CsvPath()
        c.add_to_config("errors", "csvpath", "raise, collect, print")
        c.parse(f"${PATH}[*][yes()]")
        c.new_matcher(None)
        count = Count(matcher=c.matcher, name="count")
        FunctionFactory.add_function(name="A123", function=count)

    def test_bad_function_name_5(self):
        #
        # we had not allowed _; however, _ makes a ton of sense. underscore as the
        # last char is ugly but might be useful. the grammar supports it and i don't
        # want to mess with it.
        #
        c = CsvPath()
        c.add_to_config("errors", "csvpath", "raise, collect, print")
        c.parse(f"${PATH}[*][yes()]")
        c.new_matcher(None)
        count = Count(matcher=c.matcher, name="count")
        FunctionFactory.add_function(name="count_", function=count)

    def test_bad_function_name_6(self):
        #
        # we had not allowed _; however, _ makes a ton of sense. underscore as the
        # last char is ugly but might be useful. the grammar supports it and i don't
        # want to mess with it.
        #
        c = CsvPath()
        c.add_to_config("errors", "csvpath", "raise, collect, print")
        c.parse(f"${PATH}[*][yes()]")
        c.new_matcher(None)
        count = Count(matcher=c.matcher, name="count")
        FunctionFactory.add_function(name="count.v2", function=count)

    def test_bad_function_name_7(self):
        c = CsvPath()
        c.add_to_config("errors", "csvpath", "raise, collect, print")
        c.parse(f"${PATH}[*][yes()]")
        c.new_matcher(None)
        count = Count(matcher=c.matcher, name="count")
        #
        # we can override internal count function with a new count function
        #
        FunctionFactory.add_function(name="count", function=count)

    def test_function_name(self):
        c = CsvPath()
        c.add_to_config("errors", "csvpath", "raise, collect, print")
        c.parse(f"${PATH}[*][yes()]")
        count = Count(matcher=c.matcher, name="count")
        c.fast_forward()
        name = "iamaname"
        name = FunctionFactory.qname(matcher=c.matcher, name=name)
        FunctionFactory.add_function(name, count)
        f = FunctionFactory.get_function(matcher=c.matcher, name="iamaname")
        assert f is not None
        assert isinstance(f, Function)
