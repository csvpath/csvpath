import unittest
import os
from csvpath.csvpath import CsvPath

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"


class TestFunctionsCollect(unittest.TestCase):
    def test_function_collect1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1*]
            [
                collect(1)
                print("$.csvpath.count_lines ")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 8
        assert len(lines[0]) == 1

    def test_function_collect2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1*]
            [
                collect(0, "say")
                print("$.csvpath.count_lines ")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 8
        assert len(lines[0]) == 2

    def test_function_collect25(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1*]
            [
                collect(#firstname, #say)
                print("$.csvpath.count_lines ")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 8
        assert len(lines[0]) == 2
        assert lines[0][0] == "David"

    def test_function_collect3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1*]
            [
                collect(0, "say")
                print("$.csvpath.count_lines ")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 8
        assert len(lines[0]) == 2
        assert lines[0] == ["David", "hi!"]
        assert lines[1] == ["Fish", "blurgh..."]
