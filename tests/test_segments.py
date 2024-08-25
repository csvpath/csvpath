import unittest
from csvpath.csvpath import CsvPath
import pytest

PATH = "a/test/file.csv"


class TestSegments(unittest.TestCase):
    def test_segments_find_scan_match_modify1(self):
        path = CsvPath()
        s, ma, mo = path._find_scan_match_modify(
            f"""${PATH}[3][ @frog = any(header(), "Frog") ]"""
        )
        assert s == f"${PATH}[3]"
        assert ma == """[ @frog = any(header(), "Frog") ]"""
        assert mo is None

    def test_segments_find_scan_match_modify2(self):
        # a regex with [] like this path was confusing the parts finder
        path = CsvPath()
        s, ma, mo = path._find_scan_match_modify(
            f"""${PATH}[0-7][ regex(#say, /^sniffl[Ee]/) ]"""
        )
        assert s == f"${PATH}[0-7]"
        assert ma == """[ regex(#say, /^sniffl[Ee]/) ]"""
        assert mo is None

    def test_segments_3(self):
        t1 = "$test1[*]"
        t2 = "[test2]"
        # t3 = ".test3"
        path = f"{t1}{t2}"
        print(f"\n1 path: {path}")
        csvpath = CsvPath()
        scan, match, modify = csvpath._find_scan_match_modify(path)
        print(f"1 parts: {scan}, {match}, {modify}")
        assert scan == t1
        assert match == t2
        # assert modify == t3

    def test_segments_2(self):
        t1 = "$test1[*]"
        t2 = "[test2]"
        t3 = ""
        path = f"{t1}{t2}{t3}"
        print(f"\n1 path: {path}")
        csvpath = CsvPath()
        scan, match, modify = csvpath._find_scan_match_modify(path)
        print(f"1 parts: {scan}, {match}, {modify}")
        assert scan == t1
        assert match == t2
        assert not modify
