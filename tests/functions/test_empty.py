import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"
EMPTY = f"tests{os.sep}test_resources{os.sep}empty.csv"
FOOD = f"tests{os.sep}test_resources{os.sep}food.csv"


class TestFunctionsEmpty(unittest.TestCase):
    def test_function_empty0(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*][
                @d2 = dup_lines(#0)
                empty(dup_lines(#0))
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 8

    def test_function_empty1(self):
        path = CsvPath()
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
        path.parse(
            f"""
            ${FOOD}[*]
            [
                empty(#year)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1

    def test_function_empty_many1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${FOOD}[*]
            [
                empty(#year, #food, #type)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_function_empty3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${FOOD}[1*]
            [
                empty(headers())
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_function_empty4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${FOOD}[1*]
            [
                not( empty(headers()) )
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 10

    def test_function_empty5(self):
        path = CsvPath()
        path.parse(
            f"""
            ${EMPTY}[1*]
            [
                empty(headers())
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 3

    def test_function_empty6(self):
        path = CsvPath()
        path.skip_blank_lines = False
        path.parse(
            f""" ${EMPTY}[1*][
                empty(#firstname, headers())
            ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.collect()

    def test_function_empty7(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1*]
            [
                ~ headers("test") returns False so empty() cannot return True ~
                empty(headers("test"))
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0
