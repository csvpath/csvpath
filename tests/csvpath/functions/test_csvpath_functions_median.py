import unittest
import os
from unittest import mock
from csvpath.matching.functions.stats import minf
from csvpath.csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsMedian(unittest.TestCase):
    def test_function_median(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @the_median = median(count(#lastname), "line")
                no()
            ]"""
        )
        lines = path.collect()
        assert path.variables["the_median"] == 3
        assert len(lines) == 0


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


class TestCsvPathFunctionsMedianGaps(unittest.TestCase):
    """issue #572: the running value is computed once per line, over the
    numeric values seen so far. stats_gaps.csv columns: a starts empty
    (,4,6), b has an empty middle (2,,6), c is 1,10,2."""

    def test_median_empty_first_value(self):
        # before #572 an empty first value kept the median at None on
        # every line, because median() ran on the empty prefix each time.
        assert _running(fn="median", header="a") == [None, 4.0, 5.0]

    def test_median_empty_middle_value(self):
        assert _running(fn="median", header="b") == [2.0, 2.0, 4.0]

    def test_median_running_values(self):
        assert _running(fn="median", header="c") == [1.0, 5.5, 2.0]

    def test_called_once_per_line(self):
        # before #572 median() ran once per stored value on every
        # line: 1 + 2 + 3 = 6 calls for 3 lines, O(n^3) for a run.
        with mock.patch(
            "csvpath.matching.functions.stats.minf.median", wraps=minf.median
        ) as spy:
            _running(fn="median", header="c")
        assert spy.call_count == 3
