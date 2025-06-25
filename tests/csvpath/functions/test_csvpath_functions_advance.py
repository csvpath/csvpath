import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsAdvance(unittest.TestCase):
    def test_function_advance1(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
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
        assert len(lines) == 6
        assert path.variables["cnt"] == [2, 3, 4, 7, 8, 9]

    def test_function_advance2(self):
        path = CsvPath().parse(f""" ${PATH}[1*] [ advance("please") ]""")
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.collect()

    def test_function_advance_all1(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""${PATH}[1*][
                push.onmatch("cnt", count_lines())
                count.nocontrib() == 3 -> advance_all(2)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 6
        assert path.variables["cnt"] == [2, 3, 4, 7, 8, 9]

    def test_function_advance_all2(self):
        path = CsvPath()
        path.parse(f""" ${PATH}[1*] [ advance_all("please") ]""")
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.fast_forward()
