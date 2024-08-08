import unittest
from csvpath.csvpath import CsvPath

PATH = "tests/test_resources/test.csv"
NUMBERS = "tests/test_resources/numbers.csv"


class TestFunctionsNow(unittest.TestCase):
    def test_function_now(self):
        path = CsvPath()
        # TODO: obviously this will break and need updating 1x a year
        path.parse(f'${PATH}[*][now("%Y") == "2024"]')
        lines = path.collect()
        print(f"test_function_now: lines: {len(lines)}")
        assert len(lines) == 9

    """
    # non-deterministic test, but an interesting example to keep for now
    def test_average_what_the(self):
        path = CsvPath()
        path.parse(
            f""
            ${NUMBERS}[1*]
            [
                @ave = average.test.onmatch(#count3, "line")
                @r = random(0,1)
                @c = count()
                @c2 = count_scans()
                @c3 = count_lines()
                @r == 1
                yes()
                print(count_lines()==1, "match, scan, line, random, average")
                print(yes(), "$.variables.c, $.variables.c2, $.variables.c3, $.variables.r, $.variables.ave")
            ]""
        )
        print("")
        lines = path.collect()
        print(f"test_average_what_the: path vars: {path.variables}")
        #assert path.variables["the_average"] == 2
        #assert len(lines) == 0
        """
