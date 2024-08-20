import unittest
from csvpath.csvpath import CsvPath
from datetime import date, datetime
from tests.save import Save

DATES = "tests/test_resources/dates.csv"


class TestFunctionsDate(unittest.TestCase):
    def test_function_date1(self):
        path = CsvPath()
        Save._save(path, "test_function_date1")
        path.parse(
            f"""
            ${DATES}[0-8]
            [
                push( "dates", date( #date, #format ) )
                yes()
            ]"""
        )
        path.fast_forward()
        print(f"\ntest_function_date1: path vars: {path.variables}")
        assert len(path.variables["dates"]) == 9
        assert path.variables["dates"][0] == "date"
        for i, _ in enumerate(path.variables["dates"]):
            if i == 0:
                assert isinstance(_, str)
            else:
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
