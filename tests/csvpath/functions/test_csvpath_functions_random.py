import unittest
import pytest
import os
from csvpath.matching.util.exceptions import MatchException
from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
NUMBERS = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}numbers.csv"


class TestCsvPathFunctionsRandom(unittest.TestCase):
    def test_function_random(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @r = random(0, 1)
                no()
            ]"""
        )
        lines = path.collect()
        assert path.variables["r"] == 1 or path.variables["r"] == 0
        assert len(lines) == 0

    def test_function_increment(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @i = increment.test(yes(), 3)
                @j = increment.double_check(yes(), 2)
                @k = increment.rand(random(0,1)==1, 2)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9
        assert path.variables["test"] == 9
        assert path.variables["i"] == 3
        assert path.variables["j"] == 4
        assert path.variables["double_check_increment"] == 4

    def test_function_shuffle(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[1*][
                @order = shuffle()
                push("ordering", @order)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 8
        assert "order" in path.variables
        assert path.variables["order"] is not None
        assert "ordering" in path.variables
        assert len(path.variables["ordering"]) == 8

    def test_function_shuffle2(self):
        path = CsvPath().parse(
            f"""${PATH}[1*][
                @order = shuffle(0, "five")
                push("ordering", @order)
            ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_shuffle3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1*]
            [
                @order.notnone = shuffle(0, 4)
                print("Line: $.csvpath.line_number: $.variables.order: $.headers.firstname")
                push("ordering", @order)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 4
        assert "order" in path.variables
        assert path.variables["order"] is not None
        assert "ordering" in path.variables
        assert len(path.variables["ordering"]) == 8
        assert path.variables["ordering"][0] is not None
        assert path.variables["ordering"][4] >= 0

    def test_function_shuffle4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1*]
            [
                @order.notnone = shuffle()
                @order2.notnone = shuffle()
                print("Line: $.csvpath.line_number: $.variables.order: $.variables.order2")
                push("ordering", @order)
                push("ordering2", @order2)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 4
        assert "order" in path.variables
        assert path.variables["order"] is not None
        assert "ordering" in path.variables
        assert len(path.variables["ordering"]) == 8
        assert path.variables["ordering"][0] is not None
        assert path.variables["ordering"][4] >= 0
