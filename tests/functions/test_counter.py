import unittest
import pytest
from csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsCounter(unittest.TestCase):
    def test_function_counter(self):
        path = CsvPath()
        Save._save(path, "test_function_counter")
        path.parse(
            f"""
            ${PATH}[1*][
               counter.one(5)
               print("one: $.variables.one")
               mod(@one, 10) == 0 -> counter.two(2)
               print("two: $.variables.two ")
               gt(@two, 4) -> counter.three()
               print("three: $.variables.three")
            ]"""
        )
        lines = path.collect()
        print(f"test_function_counter: lines: {lines}")
        print(f"test_function_counter: path vars: {path.variables}")
        assert path.variables["one"] == 40
        assert path.variables["two"] == 8
        assert path.variables["three"] == 3
