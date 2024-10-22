import unittest
import pytest
from csvpath import CsvPath
from tests.save import Save

EMPTY = "tests/test_resources/empty3.csv"
FOOD = "tests/test_resources/food.csv"


class TestFunctionsEmptyStack(unittest.TestCase):
    def test_function_empty_stack1(self):
        print("")
        path = CsvPath()
        Save._save(path, "test_function_empty_stack1")
        path.parse(
            f"""
            ${FOOD}[7*][
                push.notnone("empties", empty_stack(#year, #healthy) )
            ]"""
        )
        lines = path.collect()
        print(f"\n test_function_empty_stack1: lines: {lines}")
        print(f"test_function_empty_stack1: path vars: {path.variables}")
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
        Save._save(path, "test_function_empty_stack1")
        path.parse(
            f"""
            ${FOOD}[7*][
                ~ matches if len(stack) != 0
                  returns stack of empty headers, of all headers ~
                empty_stack()

            ]"""
        )
        lines = path.collect()
        print(f"\n test_function_empty_stack1: lines: {lines}")
        print(f"test_function_empty_stack1: path vars: {path.variables}")
        assert len(lines) == 1
