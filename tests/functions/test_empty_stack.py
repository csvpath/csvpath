import unittest
import os
import pytest
from csvpath import CsvPath

EMPTY = f"tests{os.sep}test_resources{os.sep}empty3.csv"
FOOD = f"tests{os.sep}test_resources{os.sep}food.csv"


class TestFunctionsEmptyStack(unittest.TestCase):
    def test_function_empty_stack1(self):
        path = CsvPath()
        path.parse(
            f"""
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

    def test_function_empty_stack2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${FOOD}[7*][
                ~ matches if len(stack) != 0
                  returns stack of empty headers, of all headers ~
                empty_stack()

            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1

    def test_function_empty_stack3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${FOOD}[1*][
                even(line_number()) -> @a.renew = line_number()
                push.notnone("empties", empty_stack(@a, #healthy) )
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 5
        assert "empties" in path.variables
        assert isinstance(path.variables["empties"], list)
        s = path.variables["empties"]
        assert len(s) == 5
        for es in s:
            assert isinstance(es, list)
            assert len(es) == 1
            assert es == ["a"]
