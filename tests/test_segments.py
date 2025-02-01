import unittest
from csvpath import CsvPath
import pytest

PATH = "a/test/file.csv"


class TestSegments(unittest.TestCase):
    def test_segments_find_scan_and_match_parts1(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise")
        s, ma = path._find_scan_and_match_parts(
            f"""${PATH}[3][ @frog = any(header(), "Frog") ]"""
        )
        assert s == f"${PATH}[3]"
        assert ma == """[ @frog = any(header(), "Frog") ]"""

    def test_segments_find_scan_match_2(self):
        # a regex with [] like this path was confusing the parts finder
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise")
        s, ma = path._find_scan_and_match_parts(
            f"""${PATH}[0-7][ regex(#say, /^sniffl[Ee]/) ]"""
        )
        assert s == f"${PATH}[0-7]"
        assert ma == """[ regex(#say, /^sniffl[Ee]/) ]"""

    def test_segments_3(self):
        t1 = "$test1[*]"
        t2 = "[test2]"
        # t3 = ".test3"
        path = f"{t1}{t2}"
        csvpath = CsvPath()
        csvpath.add_to_config("errors", "csvpath", "raise")
        scan, match = csvpath._find_scan_and_match_parts(path)
        assert scan == t1
        assert match == t2

    def test_segments_2(self):
        t1 = "$test1[*]"
        t2 = "[test2]"
        t3 = ""
        path = f"{t1}{t2}{t3}"
        csvpath = CsvPath()
        csvpath.add_to_config("errors", "csvpath", "raise")
        scan, match = csvpath._find_scan_and_match_parts(path)
        assert scan == t1
        assert match == t2
