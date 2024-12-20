import unittest
import pytest
from csvpath import CsvPath

PATH = "tests/test_resources/test.csv"


class TestFunctionsCounter(unittest.TestCase):
    def test_function_counter(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1*][
               counter.one(5)
               print("one: $.variables.one")
               mod(@one, 10) == 0 -> counter.two(2)
               print("two: $.variables.two ")
               gt(@two, 4) -> counter.three()
               print("three: $.variables.three")
               no() -> counter.four()
            ]"""
        )
        path.collect()
        assert path.variables["one"] == 40
        assert path.variables["two"] == 8
        assert path.variables["three"] == 3
        assert path.variables["four"] == 0
