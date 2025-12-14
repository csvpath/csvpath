import unittest
import os
import pytest
from csvpath.csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsRemove(unittest.TestCase):
    def test_function_remove_1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                remove(1)
                print("$.csvpath.count_lines ")

            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9
        assert len(lines[0]) == 2
        assert lines[0] == ["firstname", "say"]

    def test_function_remove_2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                remove(#1)
                print("$.csvpath.count_lines ")

            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9
        assert len(lines[0]) == 2
        assert lines[0] == ["firstname", "say"]

    def test_function_remove_3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                remove(#0,#2)
                print("$.csvpath.count_lines ")

            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9
        assert len(lines[0]) == 1
        assert lines[0] == ["lastname"]

    def test_function_remove_4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                remove(#0,#lastname,#2)
                print("$.csvpath.count_lines ")

            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9
        assert len(lines[0]) == 0
        assert lines[0] == []

    def test_function_remove_5(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise, print ~
            ${PATH}[*]
            [
                remove(#0,#firstname)
                print("$.csvpath.count_lines ")

            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_function_remove_6(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise, print ~
            ${PATH}[*]
            [
                remove(#0,#1, #2, #3)
                print("$.csvpath.count_lines ")

            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_function_remove_7(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise, print ~
            ${PATH}[*]
            [
                remove(#flipper)
                print("$.csvpath.count_lines ")

            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()
