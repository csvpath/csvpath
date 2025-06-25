import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import ChildrenException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsPercent(unittest.TestCase):
    def test_function_percent_match(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*][
                @p = percent("match")
                #lastname=="Bat"
                print("$.headers.firstname: $.csvpath.count_lines")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 7
        assert path.line_monitor.data_end_line_number == 8
        assert path.variables["p"] == 0.67

    def test_function_percent_below(self):
        path = CsvPath()
        path.parse(f'${PATH}[*][@p = percent("match")  below(@p,.35) #lastname=="Bat"]')
        lines = path.collect()
        assert len(lines) == 4
        assert path.variables["p"] == 0.44

    def test_function_percent_above(self):
        path = CsvPath()
        path.parse(f'${PATH}[*][@p=percent("line")  above(@p, .35) #lastname=="Bat"]')
        lines = path.collect()
        assert len(lines) == 6
        assert path.variables["p"] == 1

    def test_function_percent_1(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
            ${PATH}[*][
                @p = percent.onmatch("line")
            ]
        """
        )
        with pytest.raises(ChildrenException):
            path.fast_forward()
