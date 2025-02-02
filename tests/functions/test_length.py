import unittest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"


class TestFunctionsLength(unittest.TestCase):
    def test_function_length(self):
        path = CsvPath()

        path.parse(
            f"""
            ${PATH}[1]
            [ @l = length("this") ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["l"] == 4

    def test_function_length2(self):
        path = CsvPath()

        path.parse(
            f"""
            ${PATH}[1]
            [ @l = add( 4, length("this")) ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["l"] == 8

    def test_function_length3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = add( count(), length("this") ) ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["l"] == 5

    def test_function_length4(self):
        path = CsvPath()

        path.parse(
            f"""
            ${PATH}[1]
            [ @l = add( count(), length("this"), 5 ) ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["l"] == 10

    def test_function_length5(self):
        path = CsvPath()

        path.parse(
            f"""
            ${PATH}[1]
            [ @l = add( count(), length("this"), 5, 5 ) ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["l"] == 15

    def test_function_length6(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = subtract( count(), length("this") ) ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["l"] == -3

    def test_function_length7(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = subtract( 10, count(), length("this") ) ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["l"] == 5

    def test_function_length8(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [ @l = subtract( 10, count(), length("this"), add( 2, 3) ) ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["l"] == 0

    def test_function_match_length(self):
        path = CsvPath()
        path.parse(f"${PATH}[*][length(#lastname)==3]")
        lines = path.collect()
        assert len(lines) == 7

    def test_function_not_length(self):
        path = CsvPath()
        path.parse(f"${PATH}[*][not(length(#lastname)==3)]")
        lines = path.collect()
        assert len(lines) == 2

    def test_function_minmax_length1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[0-3]
            [
                push( "min", min_length( #lastname, 5))
                push( "max", max_length( #lastname, 4))
                push( "too_long", too_long( #lastname, 5))
                push( "too_short", too_short( #lastname, 4))
            ]"""
        )
        path.fast_forward()
        assert path.variables["min"] == [True, True, False, False]
        assert path.variables["max"] == [False, False, True, True]
        assert path.variables["too_long"] == [True, True, False, False]
        assert path.variables["too_short"] == [False, False, True, True]

    def test_too_long1(self):
        csvpath = """$tests/test_resources/trivial.csv[*][
                    ~ Apply three rules to check if a CSV file meets expectations ~
                      too_long(#lastname, 30)
                  ]"""
        path = CsvPath()
        path.parse(csvpath)
        lines = path.collect()
        assert len(lines) == 1

    def test_too_long2(self):
        csvpath = """$tests/test_resources/trivial.csv[*][
                    ~ Apply three rules to check if a CSV file meets expectations ~
                      or(
                        missing(headers())
                        ,
                        too_long(#lastname, 30)
                      )
                  ]"""
        path = CsvPath()
        path.parse(csvpath)
        lines = path.collect()
        assert len(lines) == 2
