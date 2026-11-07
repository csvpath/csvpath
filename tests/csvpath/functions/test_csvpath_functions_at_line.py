import unittest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsAtLine(unittest.TestCase):
    def test_function_atline_1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[0-7]
            [
                at_line(4) -> push("fish", "tuna")
                not(at_line(4)) -> push("fish", line_number())
            ]"""
        )
        path.collect()
        assert path.variables["fish"] == [0, 1, 2, 3, "tuna", 5, 6, 7]

    def test_function_atline_2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[0-7]
            [
                at_line(2, 3) -> push("fish", "three")
                at_line(4, 5) -> push("fish", "five")
                not(at_line(2, 3, 4, 5)) -> push("fish", line_number())
            ]"""
        )
        path.collect()
        assert path.variables["fish"] == [0, 1, "three", "three", "five", "five", 6, 7]

    def test_function_notline_1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[0-7]
            [
                not_line(4) -> push("fish", "tuna")
                at_line(4) -> push("fish", line_number())
            ]"""
        )
        path.collect()
        assert path.variables["fish"] == [
            "tuna",
            "tuna",
            "tuna",
            "tuna",
            4,
            "tuna",
            "tuna",
            "tuna",
        ]

    def test_function_notline_2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[0-7]
            [
                at_line(2, 3) -> push("fish", "three")
                at_line(4, 5) -> push("fish", "five")
                not_line(2, 3, 4, 5) -> push("fish", line_number())
            ]"""
        )
        path.collect()
        assert path.variables["fish"] == [0, 1, "three", "three", "five", "five", 6, 7]
