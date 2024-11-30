import unittest
from csvpath import CsvPath

PATH = "tests/test_resources/test.csv"


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
