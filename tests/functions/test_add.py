import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = "tests/test_resources/test.csv"


class TestFunctionsAdd(unittest.TestCase):
    def test_function_add1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = add( 4, length("this")) ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["l"] == 8

    def test_function_add2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = add( count(), length("this") ) ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["l"] == 5

    def test_function_add3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = add( count(), length("this"), 5 ) ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["l"] == 10

    def test_function_add4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = add( count(), length("this"), 5, 5 ) ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["l"] == 15

    def test_function_add_error1(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["raise"]
        with pytest.raises(MatchException):
            path.parse(
                f"""
                ${PATH}[1]
                [ @l = add( count() ) ]"""
            )
            path.fast_forward()
