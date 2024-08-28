import unittest
from csvpath.csvpath import CsvPath
from datetime import date, datetime
from tests.save import Save

DATES = "tests/test_resources/dates.csv"


class TestFunctionsBetween(unittest.TestCase):

    #
    # dates
    #
    def test_function_between_dates1(self):
        path = CsvPath()
        Save._save(path, "test_function_before_dates1")
        path.parse(
            f"""
            ~ date < unconverted string == False ~
            ${DATES}[1][
                @date = between( date( "2000-10-02", "%Y-%m-%d" ),
                                 date( "2000-10-01", "%Y-%m-%d" ),
                                 date( "2000-10-03", "%Y-%m-%d" ) )
                ]"""
        )
        path.fast_forward()
        print(f"\ntest_function_before_dates1: path vars: {path.variables}")
        assert path.variables["date"] is True

    def test_function_between_not_between_dates1(self):
        path = CsvPath()
        Save._save(path, "test_function_beweeen_not_between_dates")
        path.parse(
            f"""
            ~ date < unconverted string == False ~
            ${DATES}[1][
                date( "2000-10-01", "%Y-%m-%d" )
                @date = between( date( "2000-10-01", "%Y-%m-%d" ),
                                 date( "2000-10-02", "%Y-%m-%d" ),
                                 date( "2000-10-02", "%Y-%m-%d" ) )
                ]"""
        )
        path.fast_forward()
        print(
            f"\n test_function_beweeen_not_between_dates: path vars: {path.variables}"
        )
        assert path.variables["date"] is False

    def test_function_between_not_between_dates2(self):
        path = CsvPath()
        Save._save(path, "test_function_beweeen_not_between_dates")
        path.parse(
            f"""
            ~ date < unconverted string == False ~
            ${DATES}[1][
                @date = between( date( "2000-10-03", "%Y-%m-%d" ),
                                 date( "2000-10-01", "%Y-%m-%d" ),
                                 date( "2000-10-02", "%Y-%m-%d" ) )
                ]"""
        )
        path.fast_forward()
        print(
            f"\n test_function_beweeen_not_between_dates: path vars: {path.variables}"
        )
        assert path.variables["date"] is False

    def test_function_between_ints_and_floats(self):
        path = CsvPath()
        Save._save(path, "test_function_between_floats")
        path.parse(
            f"""
            ${DATES}[1][
                @i = between( 1, 0, 3 )
                @j = between( 1.3, 0.1, 3.9 )
                @k = between( 3, 1, 2 )
                @l = between( 1.1, 1, 2 )
            ]"""
        )
        path.fast_forward()
        print(f"\n test_function_between_floats: path vars: {path.variables}")
        assert path.variables["i"] is True
        assert path.variables["j"] is True
        assert path.variables["k"] is False
        assert path.variables["l"] is True

    def test_function_between_strings(self):
        path = CsvPath()
        Save._save(path, "test_function_after_dates2")
        path.parse(
            f"""
            ${DATES}[1][
                @w = between( "who", "on", "first" )
                @o = between( "on", "who", "first" )
                @f = between( "first", "on", "who" )
            ]"""
        )
        path.fast_forward()
        print(f"\ntest_function_after_dates2: path vars: {path.variables}")
        assert path.variables["w"] is False
        assert path.variables["o"] is True
        assert path.variables["f"] is False

    def test_function_between_string_and_int(self):
        path = CsvPath()
        Save._save(path, "test_function_after_dates2")
        path.parse(
            f"""
            ${DATES}[1][
                @1 = between( 1, "0", 3 )
                @2 = between( 2, "0", "9" )
                @3 = between( "3", 1, 100 )
            ]"""
        )
        path.fast_forward()
        print(f"\ntest_function_after_dates2: path vars: {path.variables}")
        assert path.variables["1"] is True
        assert path.variables["2"] is True
        assert path.variables["3"] is True
