import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException
from tests.save import Save

PATH = "tests/test_resources/test.csv"
EMPTY = "tests/test_resources/empty.csv"
FOOD = "tests/test_resources/food.csv"


class TestFunctionsEmpty(unittest.TestCase):
    def test_function_empty0(self):
        path = CsvPath()
        Save._save(path, "test_function_empty1")
        path.parse(
            f"""
            ${PATH}[*][
                @d2 = dup_lines(#0)
                empty(dup_lines(#0))
            ]"""
        )
        lines = path.collect()
        print(f"\n test_function_empty1: lines: {lines}")
        print(f"test_function_empty1: path vars: {path.variables}")
        assert len(lines) == 8

    def test_function_empty1(self):
        path = CsvPath()
        Save._save(path, "test_function_empty1")
        path.parse(
            f""" ${PATH}[*][
                @d = dup_lines()
                empty(dup_lines())
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_function_empty2(self):
        path = CsvPath()
        Save._save(path, "test_function_empty2")
        path.parse(
            f"""
            ${FOOD}[*]
            [
                empty(#year)
            ]"""
        )
        lines = path.collect()
        print(f"\n test_function_empty2: lines: {lines}")
        print(f"test_function_empty2: path vars: {path.variables}")
        assert len(lines) == 1

    def test_function_empty_many1(self):
        path = CsvPath()
        Save._save(path, "test_function_empty_many1")
        path.parse(
            f"""
            ${FOOD}[*]
            [
                empty(#year, #food, #type)
            ]"""
        )
        lines = path.collect()
        print(f"\n test_function_empty_many1: lines: {lines}")
        print(f"test_function_empty_many1: path vars: {path.variables}")
        assert len(lines) == 0

    def test_function_empty3(self):
        path = CsvPath()
        Save._save(path, "test_function_empty3")
        path.parse(
            f"""
            ${FOOD}[1*]
            [
                empty(headers())
            ]"""
        )
        lines = path.collect()
        print(f"\n test_function_empty3: lines: {lines}")
        print(f"test_function_empty3: path vars: {path.variables}")
        assert len(lines) == 0

    def test_function_empty4(self):
        path = CsvPath()
        Save._save(path, "test_function_empty4")
        path.parse(
            f"""
            ${FOOD}[1*]
            [
                not( empty(headers()) )
            ]"""
        )
        lines = path.collect()
        print(f"\n test_function_empty4: lines: {lines}")
        print(f"test_function_empty4: path vars: {path.variables}")
        assert len(lines) == 10

    def test_function_empty5(self):
        path = CsvPath()
        # path.skip_blank_lines = False
        Save._save(path, "test_function_empty5")
        path.parse(
            f"""
            ${EMPTY}[1*]
            [
                empty(headers())
            ]"""
        )
        lines = path.collect()
        print(f"\n test_function_empty5: lines: {lines}")
        print(f"test_function_empty5: path vars: {path.variables}")
        assert len(lines) == 3

    def test_function_empty6(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["raise"]
        path.skip_blank_lines = False
        Save._save(path, "test_function_empty6")
        with pytest.raises(MatchException):
            path.parse(
                f"""
                ${EMPTY}[1*]
                [
                    empty(#firstname, headers())
                ]"""
            )
            path.collect()
