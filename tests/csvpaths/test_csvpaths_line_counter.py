import unittest
import os
from csvpath.util.line_counter import LineCounter
from tests.csvpaths.builder import Builder

PATH = f"tests{os.sep}csvpaths{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathsLineCounter(unittest.TestCase):
    def test_line_counter_1(self) -> None:
        paths = Builder().build()
        counter = LineCounter(paths)
        m, lst = counter.get_lines_and_headers(PATH)
        assert m
        assert lst
        assert len(lst) == 3
        assert lst == ["firstname", "lastname", "say"]
        assert m._physical_end_line_count == 9

        m2, lst2 = counter.get_lines_and_headers(PATH)
        assert m
        assert lst
        assert len(lst) == 3
        assert lst == ["firstname", "lastname", "say"]
        assert lst == lst2
        assert m != m2
        assert m._physical_end_line_count == m2._physical_end_line_count
