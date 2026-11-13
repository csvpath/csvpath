import unittest
import os
from unittest import mock
from csvpath.matching.functions.stats import minf
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


GAPS = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}stats_gaps.csv"


def _running(*, fn: str, header: str) -> list:
    path = CsvPath()
    path.parse(
        f"""${GAPS}[1*][
            @v = FN(#HEADER)
            push("seen", @v)
        ]""".replace("FN", fn).replace("HEADER", header)
    )
    path.fast_forward()
    return path.variables["seen"]


class TestCsvPathFunctionsAverageGaps(unittest.TestCase):
    """issue #572: the running value is computed once per line, over the
    numeric values seen so far. stats_gaps.csv columns: a starts empty
    (,4,6), b has an empty middle (2,,6), c is 1,10,2."""

    def test_average_empty_first_value(self):
        # before #572 an empty first value kept the average at None on
        # every line, because mean() ran on the empty prefix each time.
        assert _running(fn="average", header="a") == [None, 4.0, 5.0]

    def test_average_empty_middle_value(self):
        assert _running(fn="average", header="b") == [2.0, 2.0, 4.0]

    def test_average_running_values(self):
        seen = _running(fn="average", header="c")
        assert seen[:2] == [1.0, 5.5]
        assert round(seen[2], 6) == round(13 / 3, 6)

    def test_called_once_per_line(self):
        # before #572 mean()/median() ran once per stored value on every
        # line: 1 + 2 + 3 = 6 calls for 3 lines, O(n^3) for a run.
        with mock.patch(
            "csvpath.matching.functions.stats.minf.mean", wraps=minf.mean
        ) as spy:
            _running(fn="average", header="c")
        assert spy.call_count == 3
