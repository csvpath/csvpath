import unittest
from csvpath.csvpath import CsvPath


class TestSegments(unittest.TestCase):
    def test_segments_3(self):
        t1 = "$test1[*]"
        t2 = "[test2]"
        t3 = ".test3"
        path = f"{t1}{t2}{t3}"
        print(f"\n1 path: {path}")
        csvpath = CsvPath()
        scan, match, modify = csvpath._find_scan_match_modify(path)
        print(f"1 parts: {scan}, {match}, {modify}")
        assert scan == t1
        assert match == t2
        assert modify == t3

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

    def test_segments_1(self):
        t1 = "$test1[*]"
        t2 = ""
        t3 = ""
        path = f"{t1}{t2}{t3}"
        print(f"\n1 path: {path}")
        csvpath = CsvPath()
        scan, match, modify = csvpath._find_scan_match_modify(path)
        print(f"1 parts: {scan}, {match}, {modify}")
        assert scan == t1
        assert not match
        assert not modify
