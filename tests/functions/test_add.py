import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import ChildrenException

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"


class TestFunctionsAdd(unittest.TestCase):
    def test_function_add0(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""~ validation-mode:raise, print ~ ${PATH}[1] [ @l = add( 1, 1 ) ]"""
        ).fast_forward()
        print(f"path.vars: {path.variables}")
        assert path.variables["l"] == 2

    def test_function_add1(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
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
        path.config.add_to_config("errors", "csvpath", "raise")
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
        path.config.add_to_config("errors", "csvpath", "raise")
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
        path.config.add_to_config("errors", "csvpath", "raise")
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
        path.parse(f""" ${PATH}[1][ @l = add( count() ) ]""")
        path.config.add_to_config("errors", "csvpath", "raise, print")
        with pytest.raises(ChildrenException):
            path.fast_forward()
