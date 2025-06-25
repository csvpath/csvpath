import unittest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
EMPTY = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}empty.csv"


class TestCsvPathFunctionsNot(unittest.TestCase):
    def test_function_not(self):
        path = CsvPath()
        path.parse(f"${PATH}[*][not(length(#lastname)==3)]")
        lines = path.collect()
        assert len(lines) == 2

    def test_function_not_2(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(
            f"""
            ${PATH}[*]
            [
                @a = odd(line_number())
                print("line $.csvpath.line_number: $.variables.a")
                not(@a.asbool, push("notchk", line_number()))

            ]"""
        )
        lines = path.collect()
        assert len(lines) == 5
        assert "notchk" in path.variables
        assert path.variables["notchk"] == [0, 2, 4, 6, 8]

    def test_function_any_function4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${EMPTY}[1-2]
            [
                @found = any(headers())
                @notfound = not(any(headers()))
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 2
        assert path.variables["found"] is False
        assert path.variables["notfound"] is True

    def test_function_not_any_function5(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1-2]
            [
                ~ this is a tricky case! it is duplicated (at least today) in
                test_header.py. there are more detailed notes there on why the
                results are what they are ~
                @found = any.onmatch(headers())
                @found2 = any(headers())
                @notfound = not(any.onmatch(headers()))
                no()
            ]"""
        )
        path.collect()
        assert path.variables["found"] is None
        assert path.variables["found2"] is True
        assert path.variables["notfound"] is False
