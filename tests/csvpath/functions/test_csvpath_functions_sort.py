import unittest
import os
from csvpath.csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsSort(unittest.TestCase):
    def test_function_sort_1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [
                push("a", 1)
                push("a", 23)
                push("a", 3)
                push("a", -2)
                sort("a")
            ]"""
        )
        path.fast_forward()
        assert "a" in path.variables
        assert path.variables["a"] == [-2, 1, 3, 23]

    def test_function_sort_2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [
                push("a", 1)
                push("a", 23)
                push("a", 3)
                push("a", -2)
                sort("a", "false")
            ]"""
        )
        path.fast_forward()
        assert "a" in path.variables
        assert path.variables["a"] == [-2, 1, 3, 23]

    def test_function_sort_3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [
                push("a", 1)
                push("a", 23)
                push("a", 3)
                push("a", -2)
                sort("a", "desc")
            ]"""
        )
        path.fast_forward()
        assert "a" in path.variables
        c = list([-2, 1, 3, 23])
        c.sort(reverse=True)
        assert path.variables["a"] == c

    def test_function_sort_4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [
                push("a", 1)
                push("a", 23)
                push("a", 3)
                push("a", -2)
                sort("a", "true")
            ]"""
        )
        path.fast_forward()
        assert "a" in path.variables
        c = list([-2, 1, 3, 23])
        c.sort(reverse=True)
        assert path.variables["a"] == c
