import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.functions.function import ChildrenException
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsAdd(unittest.TestCase):
    def test_function_add1(self):
        path = CsvPath()
        Save._save(path, "test_function_add1")
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = add( 4, length("this")) ]"""
        )
        lines = path.collect()
        print(f"test_function_add1: lines: {lines}")
        print(f"test_function_add1: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == 8

    def test_function_add2(self):
        path = CsvPath()
        Save._save(path, "test_function_add2")
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = add( count(), length("this") ) ]"""
        )
        lines = path.collect()
        print(f"test_function_add: lines: {lines}")
        print(f"test_function_add: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == 5

    def test_function_add3(self):
        path = CsvPath()
        Save._save(path, "test_function_add3")
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = add( count(), length("this"), 5 ) ]"""
        )
        lines = path.collect()
        print(f"test_function_add: lines: {lines}")
        print(f"test_function_add: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == 10

    def test_function_add4(self):
        path = CsvPath()
        Save._save(path, "test_function_add4")
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = add( count(), length("this"), 5, 5 ) ]"""
        )
        lines = path.collect()
        print(f"test_function_add: lines: {lines}")
        print(f"test_function_add: path vars: {path.variables}")
        assert len(lines) == 1
        assert path.variables["l"] == 15

    def test_function_add_error1(self):
        path = CsvPath()
        Save._save(path, "test_function_add_error1")
        with pytest.raises(ChildrenException):
            path.parse(
                f"""
                ${PATH}[1]
                [ @l = add( count() ) ]"""
            )
