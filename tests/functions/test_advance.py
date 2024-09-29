import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import ChildrenException
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsAdvance(unittest.TestCase):
    def test_function_advance1(self):
        path = CsvPath()
        Save._save(path, "test_function_advance1")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                push.onmatch("cnt", count_lines())
                print("count_lines is: $.csvpath.count_lines ")
                count.nocontrib() == 3 -> advance(2)
            ]"""
        )
        # action    physical line     data line             matches           scans
        # -----------------------------------------------------------------------------------
        # skip  0 - line_number = 0 - data_line_count = 1 - match count = 0 - scan count = 0
        # match 1 - line_number = 1 - data_line_count = 2 - match count = 1 - scan count = 1
        # match 2 - line_number = 2 - data_line_count = 3 - match count = 2 - scan count = 2
        # match 3 - line_number = 3 - data_line_count = 4 - match count = 3 -> advance(2)  3
        # skip    - line_number = 4 - data_line_count = 5 - match count = 3 - scan count = 4
        # skip    - line_number = 5 - data_line_count = 6 - match count = 3 - scan count = 5
        # match 4 - line_number = 6 - data_line_count = 7 - match count = 4 - scan count = 6
        # ...
        lines = path.collect()
        print(f"test_function_advance1: lines: {lines}")
        print(f"test_function_advance1: path vars: {path.variables}")
        assert len(lines) == 6
        assert path.variables["cnt"] == [2, 3, 4, 7, 8, 9]

    def test_function_advance2(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["raise"]
        path.parse(f""" ${PATH}[1*] [ advance("please") ]""")
        with pytest.raises(ChildrenException):
            path.collect()

    def test_function_advance_all1(self):
        path = CsvPath()
        Save._save(path, "test_function_advance_all1")
        path.parse(
            f"""
            ${PATH}[1*]
            [
                push.onmatch("cnt", count_lines())
                print("count_lines is: $.csvpath.count_lines ")
                count.nocontrib() == 3 -> advance_all(2)
            ]"""
        )
        lines = path.collect()
        print(f"test_function_advance1: lines: {lines}")
        print(f"test_function_advance1: path vars: {path.variables}")
        assert len(lines) == 6
        assert path.variables["cnt"] == [2, 3, 4, 7, 8, 9]

    def test_function_advance_all2(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["raise"]
        path.parse(f""" ${PATH}[1*] [ advance_all("please") ]""")
        with pytest.raises(ChildrenException):
            path.collect()
