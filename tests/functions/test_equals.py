import unittest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"


class TestFunctionsEquals(unittest.TestCase):
    def test_function_equals(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*] [
                @m = mod(count_lines(), 2)
                @c = count( equals( @m, 0) )
                print.onmatch("printing: count: $.csvpath.match_count")
                ~ comment ~
            ]
            """
        )
        lines = path.collect()
        assert path.variables["c"] == 5
        assert len(lines) == 9

    def test_function_neq(self):
        path = (
            CsvPath()
            .parse(
                f""" ${PATH}[*][
                @m = neq(1, 5)
                push("e", neq(3, line_number()))
            ]"""
            )
            .fast_forward()
        )
        assert path.variables["m"] is True
        e = path.variables["e"]
        e = [_ for _ in e if _ is not False]
        assert len(e) == 8
