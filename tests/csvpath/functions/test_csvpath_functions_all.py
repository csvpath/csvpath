import unittest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
EMPTY = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}empty.csv"
FOOD = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}food.csv"


class TestCsvPathFunctionsAll(unittest.TestCase):
    def test_function_all1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[3]
            [
               @a = all()
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["a"] is True

    def test_function_all2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${EMPTY}[1*]
            [
               @a.asbool = all()
               print("all.asbool: $.variables.a  $.csvpath.line_number")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0
        assert path.variables["a"] is False

    def test_function_all3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${FOOD}[10]
            [
               all()
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_function_all4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${FOOD}[10]
            [
               all(#food,#type,#units)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1

    def test_function_all5(self):
        path = CsvPath()

        path.parse(
            f"""
            ${FOOD}[*]
            [
               not(all(headers()))
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1

    def test_function_all6(self):
        path = CsvPath()
        path.parse(
            f"""
            ${FOOD}[*]
            [
                last.nocontrib() -> @noway = none()
                not(all( variables()))
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
