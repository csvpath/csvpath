import unittest
import pytest
import os
from csvpath.csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
NUMBERS = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}numbers6.csv"


class TestCsvPathFunctionsRename(unittest.TestCase):
    def test_function_rename_1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [
                rename(#0, "fish")
                @chk = #fish
            ]"""
        )
        path.fast_forward()
        assert path.variables["chk"] == "David"

    def test_function_rename_2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${NUMBERS}[1]
            [
                ~ do we recognize header #1 is named "0". No. ~

                @s = headers_stack()
                @is1 = #0
                @is2 = #1
           ]"""
        )
        path.fast_forward()
        assert path.variables["is1"] == "3.52"
        assert path.variables["is2"] == "1"

    def test_function_rename_3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${NUMBERS}[1]
            [
                ~ can we rename header named "0"? ~

                @s1 = headers_stack()
                @is1 = #1
                rename(#1, "counts")
                @s2 = headers_stack()
                @is2 = #counts
           ]"""
        )
        path.fast_forward()
        assert path.variables["is1"] == "1"
        assert path.variables["is2"] == "1"
        assert path.variables["s1"] == ["2", "0", "96", "67"]
        assert path.variables["s2"] == ["2", "counts", "96", "67"]

    def test_function_rename_4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${NUMBERS}[1]
            [
                ~ can we rename header named "0" before first use? ~
                rename(#1, "counts")
                @is1 = #counts
                @s = headers_stack()
                @is2 = #1
           ]"""
        )
        path.fast_forward()
        assert path.variables["is1"] == "1"
        assert path.variables["is2"] == "1"
        assert path.variables["s"] == ["2", "counts", "96", "67"]

    def test_function_rename_5(self):
        path = CsvPath()
        path.parse(
            f"""
            ${NUMBERS}[1]
            [
                ~
                    can we use "0" as the name of header #1, since it is the name of #1?
                    no.
                ~
                @is1 = #"0"
                @is2 = #0
                ~
                    both of these get the #0 == named "2" (not the value in the 2nd line)
                ~
                @is3 = header_name("0")
                @is4 = header_index("0")
                ~
                    both of these get the value of #0 using #1; i.e. by index, not by name
                ~
                @is5 = #1
                @is6 = #"1"
                ~
                    rename simplifies things
                ~
                rename(#0, "crawling things")
                rename(#1, "flying things")

                @is7 = #"crawling things"
                @is8 = #"flying things"

                @is9 = header_name("0")
                @is10 = header_index("1")

            ]"""
        )
        path.fast_forward()
        assert path.variables["is1"] == "3.52"
        assert path.variables["is2"] == "3.52"

        assert path.variables["is3"] == "2"
        assert path.variables["is4"] == "2"

        assert path.variables["is5"] == "1"
        assert path.variables["is6"] == "1"

        assert path.variables["is7"] == "3.52"
        assert path.variables["is8"] == "1"

        assert path.variables["is9"] == "crawling things"
        assert path.variables["is10"] == "flying things"

    def test_function_rename_6(self):
        path = CsvPath()
        path.parse(
            f"""
            ${NUMBERS}[0]
            [
                @hs1 = headers_stack()
                rename("crawling", "flying", "swimming")
                @c = #crawling
                @f = #flying
                @s = #swimming
                @x1 = #67
                @x2 = #3
                @hs2 = headers_stack()
           ]"""
        )
        path.fast_forward()
        assert path.variables["c"] == "2"
        assert path.variables["f"] == "0"
        assert path.variables["s"] == "96"
        assert path.variables["hs1"] == ["2", "0", "96", "67"]
        assert path.variables["hs2"] == ["crawling", "flying", "swimming", "67"]
        assert path.variables["x1"] is None
        assert path.variables["x2"] == "67"

    def test_function_rename_7(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise ~
            ${NUMBERS}[0]
            [
                @hs1 = headers_stack()
                rename("crawling", "flying", "swimming", "fishing", "worming")
           ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_rename_8(self):
        path = CsvPath()
        path.parse(
            f"""
            ~ validation-mode:raise ~
            ${NUMBERS}[3]
            [
                @hs1 = headers_stack()
                rename("crawling", "flying", "swimming", "fishing")
                @hs2 = headers_stack()
                @chk = #flying
                rename(@hs1)
                @hs3 = headers_stack()

           ]"""
        )
        path.fast_forward()
        assert path.variables["chk"] == "20"
        assert path.variables["hs1"] == path.variables["hs3"]
        assert path.variables["hs1"] != path.variables["hs2"]
