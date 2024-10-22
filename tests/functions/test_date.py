import unittest
import pytest
from csvpath.csvpath import CsvPath
from datetime import date, datetime
from csvpath.matching.util.exceptions import MatchException
from tests.save import Save

DATES = "tests/test_resources/dates.csv"
TEST = "tests/test_resources/test.csv"


class TestFunctionsDate(unittest.TestCase):
    def test_function_date0(self):
        path = CsvPath()
        Save._save(path, "test_function_date0")
        path.parse(
            f"""
            ${TEST}[4] [
                push( "dates", date( #firstname ) )
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_date01(self):
        path = CsvPath()
        Save._save(path, "test_function_date01")
        path.parse(
            f"""
            ${TEST}[4] [
                push( "dates", date( "2024-01-01" ) )
            ]"""
        )
        path.fast_forward()

    def test_function_date1(self):
        path = CsvPath()
        Save._save(path, "test_function_date1")
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
        print(f"\ntest_function_date1: path vars: {path.variables}")
        for d in path.variables["dates"]:
            print(f"...d: {d}")
        assert len(path.variables["dates"]) == 8
        for i, _ in enumerate(path.variables["dates"]):
            assert isinstance(_, date)

    def test_function_date2(self):
        path = CsvPath()
        Save._save(path, "test_function_date2")
        path.parse(
            f"""
            ${DATES}[9+10]
            [
                push( "dates", datetime( #date, #format ) )
            ]"""
        )
        path.fast_forward()
        print(f"\ntest_function_date2: path vars: {path.variables}")
        assert len(path.variables["dates"]) == 2
        for i, _ in enumerate(path.variables["dates"]):
            assert isinstance(_, datetime)
