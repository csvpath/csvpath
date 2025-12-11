import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import ChildrenException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsLineBefore(unittest.TestCase):
    def test_function_line_before_1(self):
        path = (
            CsvPath()
            .parse(
                f""" ${PATH}[1*][
                @before = line_before(#0)
                @last1 = line_before.s1("0")
                @last2 = line_before.s2("firstname")
                @last3 = line_before.s3(#firstname)
                push.skipnone("b", @before)
                @current = #0
             ]"""
            )
            .fast_forward()
        )
        assert path.variables["b"] == [
            "David",
            "Fish",
            "Frog",
            "Bug",
            "Bird",
            "Ants",
            "Slug",
        ]
        assert path.variables["before"] == "Slug"
        assert path.variables["current"] == "Frog"
        assert path.variables["last1"] == "Slug"
        assert path.variables["last2"] == "Slug"
        assert path.variables["last3"] == "Slug"

    def test_function_line_before_2(self):
        path = CsvPath().parse(
            f"""${PATH}[3-5][
                @b = line_before()
            ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(ChildrenException):
            path.fast_forward()
