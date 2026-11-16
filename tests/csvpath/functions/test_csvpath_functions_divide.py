import math
import unittest
import os
from csvpath.csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsDivide(unittest.TestCase):
    def test_function_divide(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[2]
            [ @l = divide( 100, 10 ) ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["l"] == 10

    def test_function_divide2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[2-3]
            [ @l = divide( 100, count() ) ]"""
        )
        lines = path.collect()
        assert len(lines) == 2
        assert path.variables["l"] == 50

    def test_function_divide3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[2-3]
            [ @l = divide( 100, count(), add(2,3) ) ]"""
        )
        lines = path.collect()
        assert len(lines) == 2
        assert path.variables["l"] == 10

    def test_function_divide4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[2-3]
            [ @l = divide( 100, 0 ) ]"""
        )
        lines = path.collect()
        assert len(lines) == 2
        import math

        assert math.isnan(path.variables["l"])


NUMBERS = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}numbers.csv"


class TestCsvPathFunctionsDivideStrings(unittest.TestCase):
    #
    # the dividend can be a string, e.g. a header value. math.isnan() was
    # called on it unconverted, raised TypeError, and to_value() swallowed
    # that, so divide(#count2, 2) was silently None. add(#count2, 1) worked.
    #

    def _value(self, expression: str, scan: str = "[1]"):
        path = CsvPath()
        path.parse(f"${NUMBERS}{scan}[ @r = {expression} ]")
        path.fast_forward()
        return path.variables["r"]

    def test_header_dividend(self):
        #
        # line 2: count2 is "10"
        #
        assert self._value("divide(#count2, 2)", scan="[2]") == 5.0

    def test_string_dividend(self):
        assert self._value('divide("10", 2)') == 5.0

    def test_string_dividend_and_divisor(self):
        assert self._value('divide("10", "4")') == 2.5

    def test_string_dividend_by_zero_is_nan(self):
        assert math.isnan(self._value('divide("10", 0)'))

    def test_three_string_arguments(self):
        assert self._value('divide("100", "2", "5")') == 10.0

    def test_every_line_of_a_header(self):
        #
        # count2 is " 1", "10", "15", then " 0" four times (note the padding)
        #
        path = CsvPath()
        path.parse(f"""${NUMBERS}[1*][ push("r", divide(#count2, 2)) ]""")
        path.collect()
        assert path.variables["r"] == [0.5, 5.0, 7.5, 0.0, 0.0, 0.0, 0.0]
