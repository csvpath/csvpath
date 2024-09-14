import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsReplace(unittest.TestCase):
    def test_function_replace1(self):
        path = CsvPath()
        Save._save(path, "test_function_replace1")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                yes()
                replace(0, count_lines())
            ]"""
        )
        lines = path.collect()
        print(f"test_function_replace1: lines: {lines}")
        assert len(lines) == 8
        assert len(lines[0]) == 3
        assert lines[0] == [2, "Kermit", "hi!"]
        assert lines[1] == [3, "Bat", "blurgh..."]

    def test_function_replace2(self):
        path = CsvPath()
        Save._save(path, "test_function_replace2")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                yes()
                replace(0, count_lines())
                replace(1, concat(#1, ", a friendly animal"))
            ]"""
        )
        lines = path.collect()
        print(f"test_function_replace2: lines: {lines}")
        assert len(lines) == 8
        assert len(lines[0]) == 3
        assert lines[0] == [2, "Kermit, a friendly animal", "hi!"]
        assert lines[1] == [3, "Bat, a friendly animal", "blurgh..."]
