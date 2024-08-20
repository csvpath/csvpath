import unittest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsEquals(unittest.TestCase):
    def test_function_equals(self):
        path = CsvPath()
        Save._save(path, "test_function_equals")
        path.parse(
            f""" ${PATH}[*] [
                @m = mod(count_lines(), 2)
                @c = count( equals( @m, 0) )
                print.onmatch("printing: $.variables, count: $.match_count")
                ~ comment ~
            ]
            """
        )
        print("")
        lines = path.collect()
        print(f"test_function_equals: path vars: {path.variables}")
        print(f"test_function_equals: lines: {lines}")
        assert path.variables["c"] == 5
        assert len(lines) == 9
