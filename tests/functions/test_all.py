import unittest
from csvpath import CsvPath

PATH = "tests/test_resources/test.csv"
EMPTY = "tests/test_resources/empty.csv"
FOOD = "tests/test_resources/food.csv"


class TestFunctionsAll(unittest.TestCase):
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
