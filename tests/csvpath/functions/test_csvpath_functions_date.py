import unittest
import os
import pytest
from datetime import date, datetime
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException, ChildrenValidationException

DATES = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}dates.csv"
PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsDate(unittest.TestCase):
    def test_function_date0(self):
        path = CsvPath().parse(
            f""" ~ validation-mode: raise ~ ${PATH}[4] [
                push( "dates", date( #firstname ) )
            ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_date1(self):
        path = CsvPath().parse(
            f"""
            ${PATH}[4] [
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

    def test_function_date4(self):
        path = CsvPath().parse(
            f"""
            ${PATH}[4] [
                push( "dates", date( "2024-01-01" ) )
                push( "dates", date( "Jan 1 2024" ) )
                push( "dates", date( "1 Jan 2024" ) )
                push( "dates", date( "January 1, 2024" ) )
                push( "dates", date( "1/21/2024" ) )
                push( "dates", date( "01/13/2024" ) )
                push( "dates", date( "13/01/2024" ) )
                @adate = "Jan 1 2024"
                push( "dates", date( @adate ) )
            ]"""
        )
        path.fast_forward()
        assert len(path.variables) == 2
        assert "dates" in path.variables
        assert len(path.variables["dates"]) == 8
        for _ in path.variables["dates"]:
            assert isinstance(_, date)
