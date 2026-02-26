import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsFingerprint(unittest.TestCase):
    def test_function_fingerprint_1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[3-6]
            [
                last() -> file_fingerprint()
                last() -> file_fingerprint.hash()
            ]"""
        )
        path.collect()
        assert "file_fingerprint" in path.metadata
        assert "hash" in path.metadata
        assert path.metadata["hash"] == path.metadata["file_fingerprint"]

    def test_function_fingerprint_2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                line_fingerprint()
                last() -> store_line_fingerprint()
            ]"""
        )
        path.collect()
        assert "by_line_fingerprint" in path.metadata
        assert "by_line_fingerprint" not in path.variables

    def test_function_fingerprint_4(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [
                @f = fingerprint()
                @1 = fingerprint(#1)
            ]"""
        )
        path.fast_forward()
        assert "f" in path.variables
        print(f"vars: {path.variables}")
        assert (
            path.variables["f"]
            == "094f17aa776da36b074d73cc1e27ecb88ddc3d04ea02d011e3efcce45eb636dd"
        )
        assert "1" in path.variables
        assert (
            path.variables["1"]
            == "cceea099c4a18adb1e406f876051031b98532bf845253c6f639a32b812c44960"
        )
