import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsOr(unittest.TestCase):
    def test_function_or_match1(self):
        path = CsvPath()
        Save._save(path, "test_function_or_match1")
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
        print(f"test_function_or_match1: lines: {lines}")
        print(f"test_function_or_match1: path vars: {path.variables}")
        assert len(lines) == 3
        assert path.variables["say"] == "oozeeee..."
        assert path.variables["line"] == 7

    def test_function_count_or_match2(self):
        path = CsvPath()
        Save._save(path, "test_function_count_or_match2")
        path.parse(
            f"""
            ${PATH}[*]
            [
                @interesting.onmatch = count()
                or(#firstname=="Fish", #lastname=="Kermit", #say=="oozeeee...")
            ]"""
        )
        lines = path.collect()
        print(f"test_function_count_or_match2: path vars: {path.variables}")
        assert path.variables["interesting"] == 3
        assert len(lines) == 3
