import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsSlice(unittest.TestCase):
    def test_function_slice_1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [
                push("a", 1)
                push("a", 23)
                push("a", 3)
                push("a", -2)
                @b = slice("a", 1, 2)
            ]"""
        )
        path.fast_forward()
        assert "b" in path.variables
        assert path.variables["b"] == [23, 3]

    def test_function_slice_2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [
                push("a", 1)
                push("a", 23)
                push("a", 3)
                push("a", -2)
                @b = slice("a", 0, 2)
            ]"""
        )
        path.fast_forward()
        assert "b" in path.variables
        assert path.variables["b"] == [1, 23, 3]

    def test_function_slice_3(self):
        path = CsvPath()
        path.parse(
            f""" ~ validation-mode:raise, collect~
            ${PATH}[1]
            [
                push("a", 1)
                push("a", 23)
                push("a", 3)
                push("a", -2)
                @b = slice("a", 2, 0)
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_slice_4(self):
        path = CsvPath()
        path.parse(
            f""" ~ validation-mode:raise, collect~
            ${PATH}[1]
            [
                push("a", 1)
                push("a", 23)
                push("a", 3)
                push("a", -2)
                @b = slice("a", -1, 0)
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_slice_5(self):
        path = CsvPath()
        path.parse(
            f""" ~ validation-mode:raise, collect~
            ${PATH}[1]
            [
                push("a", 1)
                push("a", 23)
                push("a", 3)
                push("a", -2)
                @b = slice("a", 1, 20)
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_slice_6(self):
        path = CsvPath()
        path.parse(
            f""" ~ validation-mode:raise, collect~
            ${PATH}[1]
            [
                push("a", 1)
                push("a", 23)
                push("a", 3)
                push("a", -2)
                @b = slice("c", 1, 3)
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()


#
# the end index is optional: without it the slice runs to the end of the
# stack. it used to compare the start index with None, a TypeError that
# was silently swallowed, leaving the value None.
#
def _open_end(*, pushes: str, call: str):
    path = CsvPath()
    path.config.add_to_config("errors", "csvpath", "raise, collect")
    path.parse(f"${PATH}[1][ {pushes} @b = {call} ]")
    path.fast_forward()
    assert len(path.errors) == 0
    return path.variables["b"]


@pytest.mark.parametrize(
    "call,expected",
    [
        ('slice("a", 0)', [1, 23, 3, -2]),
        ('slice("a", 1)', [23, 3, -2]),
        ('slice("a", 3)', [-2]),
    ],
)
def test_slice_without_end_runs_to_the_end(call, expected):
    pushes = 'push("a", 1) push("a", 23) push("a", 3) push("a", -2)'
    assert _open_end(pushes=pushes, call=call) == expected


def test_slice_without_end_equals_slice_to_last_index():
    pushes = 'push("a", 1) push("a", 23) push("a", 3)'
    assert _open_end(pushes=pushes, call='slice("a", 1)') == _open_end(
        pushes=pushes, call='slice("a", 1, 2)'
    )


def test_slice_without_end_of_a_negative_start_is_an_error():
    path = CsvPath()
    path.config.add_to_config("errors", "csvpath", "collect")
    path.parse(f'${PATH}[1][ push("a", 1) @b = slice("a", -1) ]')
    path.fast_forward()
    assert len(path.errors) == 1
