import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
REGEXES = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}regexes.txt"


class TestCsvPathFunctionsRegex(unittest.TestCase):
    def test_function_exact(self):
        path = CsvPath()
        path.parse(
            rf"""
            ${PATH}[0-3]
            [
                push( "e", exact( /blurgh\.\.\./, #2  ) )
                push( "ne", exact( /blurgh/, #2 ) )
                push( "r", regex( /blurgh/, #2  ) )
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 4
        assert path.variables["e"] == [False, False, True, False]
        assert path.variables["ne"] == [False, False, False, False]
        assert path.variables["r"] == [None, None, "blurgh", None]

    def test_function_regex_quick_parse(self):
        path = CsvPath()

        path.parse(
            rf"""
            ${PATH}[1]
            [
                regex( /.{0, 2}/, #0 )
            ]"""
        )

    def test_function_regex_right(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[0*] [
                regex(#say, /sniffle/)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1

    def test_function_regex1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[0-7]
            [
                regex(/sniffle/, #say)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1

    def test_function_regex2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                regex(/s(niff)le/, #say)
                @group1.onmatch = regex(/s(niff)le/, #say, 1)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert "group1" in path.variables
        assert path.variables["group1"] == "niff"

    def test_function_regex3(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["raise"]
        path.parse(
            f"""
            ${PATH}[*]
            [
                regex(/s(niff)le/, #say)
                @group1.onmatch = regex(/s(niff)le/, #say, 11)
            ]"""
        )
        with pytest.raises(IndexError):
            path.collect()

    def test_function_bad_regex1(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["raise"]
        with pytest.raises(Exception):
            path.parse(f"""${PATH}[0-7][regex(/`\\&`\\_\\L\\J/, #say)]""")  # noqa: W605
            path.collect()

    def test_function_good_regex1(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*][
                            regex(/^sniffl[Ee]/, #say)
                            @sniffle = regex(/^sniffl[Ee]/, #say)
                        ]"""
        )
        path.fast_forward()

    def test_function_headers_regex_0(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*][
                regex(headers(), /[ia]/)
             ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_function_headers_regex_1(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*][
                regex(headers(), /[y]/)
             ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_function_headers_regex_2(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*][
                regex(headers(), /sayx|firstx|lastx/)
             ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_function_regex_units(self):
        #
        # The 200+ regex in tests/test_resources/regexes.txt
        # were taken from the Python regex unit tests. They are
        # positive cases only. some lines with syntax weirdness
        # that didn't seem to have anything to do with regex testing
        # removed. (could be an artifact of my regexes used to
        # extract theirs?) also removed these 7 cases that don't
        # work and may or may not come back to bite us.
        #
        """
        $[*][regex("()ef", #0)]
        $[*][regex("()ef", #0)]
        $[*][regex("a\\(b", #0)]
        $[*][regex("a\\(b", #0)]
        $[*][regex("(?i)a\\(b", #0)]
        $[*][regex("(?i)a\\(*b", #0)]
        $[*][regex("(?<!\\?)"(.*?)(?<!\\?)"", #0)]
        """
        with open(REGEXES) as file:
            for i, line in enumerate(file):
                line = line.strip()
                path = CsvPath()
                path.parse(line, disposably=True)
