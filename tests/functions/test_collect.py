import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsCollect(unittest.TestCase):
    def test_function_collect1(self):
        path = CsvPath()
        Save._save(path, "test_function_collect1")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                collect(1)
                print("$.csvpath.count_lines ")
            ]"""
        )
        lines = path.collect()
        print(f"test_function_collect1: lines: {lines}")
        assert len(lines) == 8
        assert len(lines[0]) == 1

    def test_function_collect2(self):
        path = CsvPath()
        Save._save(path, "test_function_collect2")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                collect(0, "say")
                print("$.csvpath.count_lines ")
            ]"""
        )
        lines = path.collect()
        print(f"test_function_collect2: lines: {lines}")
        assert len(lines) == 8
        assert len(lines[0]) == 2

    def test_function_collect3(self):
        path = CsvPath()
        Save._save(path, "test_function_collect3")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                collect(0, "say")
                print("$.csvpath.count_lines ")
            ]"""
        )
        lines = path.collect()
        print(f"test_function_collect3: lines: {lines}")
        assert len(lines) == 8
        assert len(lines[0]) == 2
        assert lines[0] == ["David", "hi!"]
        assert lines[1] == ["Fish", "blurgh..."]
