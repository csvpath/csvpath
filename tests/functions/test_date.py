import unittest
import pytest
from csvpath import CsvPath
from datetime import date, datetime
from csvpath.matching.util.exceptions import MatchException, ChildrenValidationException

DATES = "tests/test_resources/dates.csv"
TEST = "tests/test_resources/test.csv"


class TestFunctionsDate(unittest.TestCase):
    def test_function_date0(self):
        path = CsvPath().parse(
            f""" ~ validation-mode: raise ~ ${TEST}[4] [
                push( "dates", date( #firstname ) )
            ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_date1(self):
        path = CsvPath().parse(
            f"""
            ${TEST}[4] [
                push( "dates", date( "2024-01-01" ) )
            ]"""
        )
        path.fast_forward()

    def test_function_date2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${DATES}[1-8]
            [
                print("line $.csvpath.line_number")
                push( "dates", date( #date, #format ) )
                yes()
            ]"""
        )
        path.fast_forward()
        assert len(path.variables["dates"]) == 8
        for i, _ in enumerate(path.variables["dates"]):
            assert isinstance(_, date)

    def test_function_date3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${DATES}[9+10]
            [
                push( "dates", datetime( #date, #format ) )
            ]"""
        )
        path.fast_forward()
        assert len(path.variables["dates"]) == 2
        for i, _ in enumerate(path.variables["dates"]):
            assert isinstance(_, datetime)
