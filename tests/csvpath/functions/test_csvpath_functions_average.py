import unittest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
NUMBERS = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}numbers.csv"


class TestCsvPathFunctionsAverage(unittest.TestCase):
    def test_function_average1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[3-5]
            [
                @the_average = average(count(), "match")
                no()
            ]"""
        )
        lines = path.collect()
        assert path.variables["the_average"] is None
        assert len(lines) == 0

    def test_function_average2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[3-5]
            [
                @the_average = average(count(#lastname), "scan")
                no()
            ]"""
        )
        lines = path.collect()
        assert path.variables["the_average"] == 2
        assert len(lines) == 0

    """
    # non-deterministic test, but a good example to keep for now
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
        lines = path.collect()
        #assert path.variables["the_average"] == 2
        #assert len(lines) == 0
        """
