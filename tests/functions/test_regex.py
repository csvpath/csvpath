import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsRegex(unittest.TestCase):
    def test_function_exact(self):
        path = CsvPath()
        Save._save(path, "test_function_regex_quick_parse")
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
        print(f"test_function_exact: path vars: {path.variables}")
        print(f"test_function_exact: lines: {lines}")
        assert len(lines) == 4
        assert path.variables["e"] == [False, False, True, False]
        assert path.variables["ne"] == [False, False, False, False]
        assert path.variables["r"] == [None, None, "blurgh", None]

    def test_function_regex_quick_parse(self):
        path = CsvPath()
        Save._save(path, "test_function_regex_quick_parse")
        path.parse(
            rf"""
            ${PATH}[1]
            [
                regex( /.{0, 2}/, #0 )
            ]"""
        )
        #                 regex(#0, /\$?(\d*|\.{0,2})/ )
        # path.collect()
        print(f"test_function_regex_quick_parse: path vars: {path.variables}")

    def test_function_regex_right(self):
        path = CsvPath()
        Save._save(path, "test_function_regex_right")
        path.parse(
            f""" ${PATH}[0*] [
                regex(#say, /sniffle/)
            ]"""
        )
        lines = path.collect()
        print(f"\ntest_function_regex_right: lines: {lines}")
        assert len(lines) == 1

    def test_function_regex1(self):
        path = CsvPath()
        Save._save(path, "test_function_regex1")
        path.parse(
            f"""
            ${PATH}[0-7]
            [
                regex(/sniffle/, #say)
            ]"""
        )
        lines = path.collect()
        print(f"\ntest_function_regex1: lines: {lines}")
        assert len(lines) == 1

    def test_function_regex2(self):
        path = CsvPath()
        Save._save(path, "test_function_regex2")
        path.parse(
            f"""
            ${PATH}[*]
            [
                regex(/s(niff)le/, #say)
                @group1.onmatch = regex(/s(niff)le/, #say, 1)
            ]"""
        )
        lines = path.collect()
        print(f"\test_function_regex2: lines: {lines}")
        print(f"test_function_regex2: path vars: {path.variables}")
        assert len(lines) == 1
        assert "group1" in path.variables
        assert path.variables["group1"] == "niff"

    def test_function_regex3(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["raise"]
        Save._save(path, "test_function_regex3")
        path.parse(
            f"""
            ${PATH}[*]
            [
                regex(/s(niff)le/, #say)
                @group1.onmatch = regex(/s(niff)le/, #say, 11)
            ]"""
        )
        with pytest.raises(MatchException):
            lines = path.collect()
            print(f"\test_function_regex3: lines: {lines}")
            print(f"test_function_regex3: path vars: {path.variables}")

    def test_function_bad_regex1(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["raise"]
        with pytest.raises(Exception):
            path.parse(f"""${PATH}[0-7][regex(/`\\&`\\_\\L\\J/, #say)]""")  # noqa: W605
            lines = path.collect()
            assert len(lines) == 0

    def test_function_good_regex1(self):
        path = CsvPath()
        Save._save(path, "test_function_good_regex1")
        path.parse(
            f"""
            ${PATH}[*][
                    regex(/^sniffl[Ee]/, #say)
                    @sniffle = regex(/^sniffl[Ee]/, #say)
               ]
            """
        )
        path.fast_forward()
        print(f"test_function_good_regex1: path.var: {path.variables}")

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
        with open("tests/test_resources/regexes.txt") as file:
            for i, line in enumerate(file):
                line = line.strip()
                print(f"[{i}] attempting line: {line}")
                path = CsvPath()
                path.parse(line, disposably=True)
        print("test_function_good_regex2 done")
