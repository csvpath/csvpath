import unittest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"


class TestFunctionsOr(unittest.TestCase):
    def test_function_or_match1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                or(#firstname=="Fish", #lastname=="Kermit", #say=="oozeeee...")
                @say.onmatch=#say
                @line.onmatch=count_lines()
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 3
        assert path.variables["say"] == "oozeeee..."
        assert path.variables["line"] == 8

    def test_function_count_or_match2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @interesting.onmatch = count()
                or(#firstname=="Fish", #lastname=="Kermit", #say=="oozeeee...")
            ]"""
        )
        lines = path.collect()
        assert path.variables["interesting"] == 3
        assert len(lines) == 3
