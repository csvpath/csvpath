import unittest
import os
from csvpath.csvpath import CsvPath
from datetime import date, datetime

DATES = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}dates.csv"


class TestCsvPathFunctionsBefore(unittest.TestCase):
    def test_function_before_dates1(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
            ~ date < unconverted string == False ~
            ${DATES}[1][
                @date = before( date( "2000-10-20", "%Y-%m-%d" ), "2002-10-20")   ]"""
        )
        path.fast_forward()
        assert path.variables["date"] is True

    def test_function_before_dates2(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
            ~ date < date == True ~
            ${DATES}[1][
                @date = before( date( "2001-10-20", "%Y-%m-%d" ), date("2002-10-20", "%Y-%m-%d" ) ) ]"""
        )
        path.fast_forward()
        assert path.variables["date"] is True

    def test_function_after_dates1(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
            ~ date > unconverted string == False ~
            ${DATES}[1][
                @date = after( date( "2000-10-20", "%Y-%m-%d" ), "2002-10-20")   ]"""
        )
        path.fast_forward()
        assert path.variables["date"] is False

    def test_function_after_dates2(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
            ~ date > date == True ~
            ${DATES}[1][
                @date_one = date("2010-10-20", "%Y-%m-%d" )
                @date_two = date("2002-10-20", "%Y-%m-%d" )
                print("one: $.variables.date_one")
                print("two: $.variables.date_two")
                @date = after(
                            @date_one,
                            @date_two
                ) ]"""
        )
        path.fast_forward()
        assert path.variables["date"] is True

    #
    # numbers
    #
    def test_function_before_int1(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
            ~ int < unconverted string == True ~
            ${DATES}[1][
                @i = before( 12, "24" ) ]"""
        )
        path.fast_forward()
        assert path.variables["i"] is True

    def test_function_before_int2(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
            ~ int < int == True ~
            ${DATES}[1][
                @i = before( 12, 24 ) ]"""
        )
        path.fast_forward()
        assert path.variables["i"] is True

    def test_function_after_int1(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
            ~ int > unconverted string == False ~
            ${DATES}[1][
                @i = after( 25, "24" ) ]"""
        )
        path.fast_forward()
        assert path.variables["i"] is True

    def test_function_after_int2(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
            ~ int > int == True ~
            ${DATES}[1][
                @i = after( 25, 24 ) ]"""
        )
        path.fast_forward()
        assert path.variables["i"] is True

    #
    # strings
    #
    def test_function_before_string1(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
            ~ string < unconverted float == True ~
            ${DATES}[1][
                @s = before( "12", 24.0 ) ]"""
        )
        path.fast_forward()
        assert path.variables["s"] is True

    def test_function_before_string2(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
            ~ string < string == True ~
            ${DATES}[1][
                @s = before( 12, 24 ) ]"""
        )
        path.fast_forward()
        assert path.variables["s"] is True

    def test_function_after_string1(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise, print")
        path.parse(
            f"""
            ~ string > unconverted float == True ~
            ${DATES}[1][
                @s = after( 25, 24.0 ) ]"""
        )
        path.fast_forward()
        assert path.variables["s"] is True

    def test_function_after_string2(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
            ~ string > string == True ~
            ${DATES}[1][
                @s = after( 25, 24 ) ]"""
        )
        path.fast_forward()
        assert path.variables["s"] is True

    def test_function_after_int_float(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
            ~ string > string == True ~
            ${DATES}[1][
                @s = gt( int(25), none() ) ]"""
        )
        path.fast_forward()
        assert path.variables["s"] is False

    def test_function_before_float_int_1(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
            ~ string < string == True ~
            ${DATES}[1-3][
                @s = below( 100.0, 90 )
                @t = below( 100, 90 )
            ]
            """
        )
        path.fast_forward()
        assert path.variables["s"] is False
        assert path.variables["t"] is False

    def test_function_before_float_int_2(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
            ~ string < string == True ~
            ${DATES}[1-3][
                @s = below( 80.0, 90 )
                @t = below( 80, 90 )
                @u = below( 80, 90.5 )
                @v = below( 80.5, 90.5 )
            ]
            """
        )
        path.fast_forward()
        assert path.variables["s"] is True
        assert path.variables["t"] is True
        assert path.variables["u"] is True
        assert path.variables["v"] is True

    def test_function_before_float_str(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
            ~ string < string == True ~
            ${DATES}[1][
                @s = below( 12.1, "24" ) ]"""
        )
        path.fast_forward()
        assert path.variables["s"] is True
