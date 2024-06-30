import unittest
import os
import shutil
import logging
import inspect
from csvpath.csvpath import CsvPath

PATH = "tests/test_resources/test.csv"

class TestCsvPath(unittest.TestCase):


    def test_includes(self):
        csvpath = CsvPath()
        # pass line number = None probably in error
        assert not csvpath._includes(None)
        # is 3 in all lines?
        assert csvpath._includes(3, from_line=None, to_line=None, all_lines=True)
        # is 3 >= 2?
        assert csvpath._includes(3, from_line=2, to_line=None, all_lines=True)
        # is 1 >= 2?
        assert not csvpath._includes(1, from_line=2, to_line=None, all_lines=True)
        # 3 = 3
        assert csvpath._includes(3, from_line=3)
        # 3 is within 2 - 4
        assert csvpath._includes(3, from_line=2, to_line=4)
        # 1 is not within 2 - 4
        assert not csvpath._includes(1, from_line=2, to_line=4)
        # 3 is in (3,5,8)
        assert csvpath._includes(3, these=[3,5,8])
        # 4 is not in (3,5,8)
        assert not csvpath._includes(4, these=[3,5,8])
        # 3 is in 0 - 4
        assert csvpath._includes(3, to_line=4)
        # 5 is not in 0 - 4
        assert not csvpath._includes(5, to_line=4)

    def test_line_numbers(self):
        csvpath = CsvPath()
        assert [1,2,3] == csvpath._collect_line_numbers(these=[1,2,3])
        assert [1,2,3] == csvpath._collect_line_numbers(from_line=1, to_line=3)
        assert ["3..."] == csvpath._collect_line_numbers(from_line=3, all_lines=True)
        assert [3] == csvpath._collect_line_numbers(from_line=3)
        assert ["0..3"] == csvpath._collect_line_numbers(to_line=3)

    def test_variables(self):
        path = CsvPath()
        scanner = path.parse(f'${PATH}[2-4][@me = count()]')
        print(f"{scanner}")
        for i, ln in enumerate(path.next()):
            assert path.get_variable("me") == i+1
            print(f'...{i} = {path.get_variable("me")}')


