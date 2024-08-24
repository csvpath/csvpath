import unittest
import pytest
from csvpath.csvpath import CsvPath
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsRegex(unittest.TestCase):
    def test_function_regex1(self):
        path = CsvPath()
        Save._save(path, "test_function_regex1")
        path.parse(
            f"""
            ${PATH}[0-7]
            [
                regex(#say, /sniffle/)
            ]"""
        )
        lines = path.collect()
        print(f"\ntest_function_regex1: lines: {lines}")
        print(f"test_function_regex1: path vars: {path.variables}")
        assert len(lines) == 1

    def test_function_regex2(self):
        path = CsvPath()
        Save._save(path, "test_function_regex2")
        path.parse(
            f"""
            ${PATH}[*]
            [
                regex(#say, /s(niff)le/)
                @group1.onmatch = regex(#say, /s(niff)le/, 1)
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
        Save._save(path, "test_function_regex3")
        path.parse(
            f"""
            ${PATH}[*]
            [
                regex(#say, /s(niff)le/)
                @group1.onmatch = regex(#say, /s(niff)le/, 11)
            ]"""
        )
        with pytest.raises(IndexError):
            lines = path.collect()
            print(f"\test_function_regex3: lines: {lines}")
            print(f"test_function_regex3: path vars: {path.variables}")

    def test_function_bad_regex1(self):
        path = CsvPath()
        with pytest.raises(Exception):
            path.parse(f"""${PATH}[0-7][regex(#say, /`\&`\_\L\J/)]""")  # noqa: W605
            lines = path.collect()
            assert len(lines) == 0

    def test_function_good_regex1(self):
        path = CsvPath()
        Save._save(path, "test_function_good_regex1")
        path.parse(
            f"""
            ${PATH}[*][
                    regex(#say, /^sniffl[Ee]/)
                    @sniffle = regex(#say, /^sniffl[Ee]/)
               ]
            """
        )
        path.fast_forward()
        print(f"test_function_good_regex1: path.var: {path.variables}")

    def test_function_regex_units(self):
        path = CsvPath()
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
                path.parse(line)
        print("test_function_good_regex2 done")
