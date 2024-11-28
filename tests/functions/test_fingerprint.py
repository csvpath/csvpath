import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = "tests/test_resources/test.csv"


class TestFunctionsFingerprint(unittest.TestCase):
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

    def test_function_fingerprint_3(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                line_fingerprint.hash()
                last() -> store_line_fingerprint()
            ]"""
        )
        #
        # not a particularly meaningful test, but it is good to
        # know the behavior. the underlying is KeyError because
        # we don't have the same name for line vs. store. we could
        # try to figure it out, but that would be error prone and
        # brittle.
        #
        with pytest.raises(MatchException):
            path.collect()
