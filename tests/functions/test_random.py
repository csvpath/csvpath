import unittest
import pytest
from csvpath.matching.util.exceptions import MatchException
from csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"
NUMBERS = "tests/test_resources/numbers.csv"


class TestFunctionsRandom(unittest.TestCase):

    """
    # non-deterministic test, but a good example to keep for now
    def test_average_what_the(self):
        path = CsvPath()
        path.parse(
            f""
            ${NUMBERS}[1*]
            [
                @ave = average.test.onmatch(#count3, "line")
                @r = random(0,1)
                @c = count()
                @c2 = count_scans()
                @c3 = count_lines()
                @r == 1
                yes()
                print(count_lines()==1, "match, scan, line, random, average")
                print(yes(), "$.variables.c, $.variables.c2, $.variables.c3, $.variables.r, $.variables.ave")
            ]""
        )
        print("")
        lines = path.collect()
        print(f"test_average_what_the: path vars: {path.variables}")
        #assert path.variables["the_average"] == 2
        #assert len(lines) == 0
    """

    def test_function_random(self):
        path = CsvPath()
        Save._save(path, "test_function_random")
        path.parse(
            f"""
            ${PATH}[*]
            [
                @r = random(0, 1)
                no()
            ]"""
        )
        lines = path.collect()
        print(f"test_function_random: path vars: {path.variables}")
        assert path.variables["r"] == 1 or path.variables["r"] == 0
        assert len(lines) == 0

    def test_function_increment(self):
        path = CsvPath()
        Save._save(path, "test_function_increment")
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
        print(f"test_function_increment: path vars: {path.variables}")
        assert len(lines) == 9
        assert path.variables["test"] == 9
        assert path.variables["i"] == 3
        assert path.variables["j"] == 4
        assert path.variables["double_check_increment"] == 4

    def test_function_shuffle(self):
        path = CsvPath()
        Save._save(path, "test_function_shuffle")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                @order = shuffle()
                print("Line: $.csvpath.line_number: $.variables.order: $.headers.firstname")
                push("ordering", @order)
            ]"""
        )
        lines = path.collect()
        print(f"test_function_shuffle: path vars: {path.variables}")
        assert len(lines) == 8
        assert "order" in path.variables
        assert path.variables["order"] is not None
        assert "ordering" in path.variables
        assert len(path.variables["ordering"]) == 8

    def test_function_shuffle2(self):
        path = CsvPath()
        Save._save(path, "test_function_shuffle")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                @order = shuffle(0, "five")
                print("Line: $.csvpath.line_number: $.variables.order: $.headers.firstname")
                push("ordering", @order)
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_shuffle3(self):
        path = CsvPath()
        Save._save(path, "test_function_shuffle3")
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
        print(f"test_function_shuffle3: path vars: {path.variables}")
        assert len(lines) == 4
        assert "order" in path.variables
        assert path.variables["order"] is not None
        assert "ordering" in path.variables
        assert len(path.variables["ordering"]) == 8
        assert path.variables["ordering"][0] is not None
        assert path.variables["ordering"][4] >= 0

    def test_function_shuffle4(self):
        path = CsvPath()
        Save._save(path, "test_function_shuffle4")
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
        print(f"test_function_shuffle3: path vars: {path.variables}")
        assert len(lines) == 4
        assert "order" in path.variables
        assert path.variables["order"] is not None
        assert "ordering" in path.variables
        assert len(path.variables["ordering"]) == 8
        assert path.variables["ordering"][0] is not None
        assert path.variables["ordering"][4] >= 0
