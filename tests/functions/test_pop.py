import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = "tests/test_resources/test.csv"
FOOD = "tests/test_resources/food.csv"


class TestPop(unittest.TestCase):
    def test_function_push1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                push("pushed", count_lines())
                @popped = pop("pushed")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9
        assert len(path.variables["pushed"]) == 0
        assert path.variables["popped"] == 9

    def test_function_push2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                no()
                push.notnone("pushed", none())
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_push3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                push.notnone("pushed", yes() )
                push("pushed2", yes() )
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9
        assert "pushed" in path.variables
        assert len(path.variables["pushed"]) == 9

    def test_function_push4(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ test is a dupe from empty_stack. keeping in case the
              functions vary independently ~
            ${FOOD}[7*][
                push.notnone("empties", empty_stack(#year, #healthy) )
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 4
        assert "empties" in path.variables
        assert isinstance(path.variables["empties"], list)
        s = path.variables["empties"]
        assert len(s) == 1
        s2 = s[0]
        assert isinstance(s2, list)
        assert len(s2) == 1
        assert s2 == ["year"]

    def test_function_peek(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                push_distinct("pushed", #lastname )
                push.distinct("dis", #lastname )
                ~ who was second? ~
                @peek = peek("dis", 1)
                @peeksize = peek_size("dis")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9
        assert len(path.variables["pushed"]) == 3
        assert len(path.variables["dis"]) == 3
        assert path.variables["peek"] == "Kermit"
        assert path.variables["peeksize"] == 3

    def test_function_pop1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                push("pushed", count_lines())
                @popped = pop("pushed")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9
        assert len(path.variables["pushed"]) == 0
        assert path.variables["popped"] == 9

    def test_function_stack1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @r = stack("st")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9
        assert path.variables["r"] == []

    def test_function_stack2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[2+3]
            [
                push("st", #1)
                @r = stack("st")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 2
        assert path.variables["r"] == ["Bat", "Bat"]
