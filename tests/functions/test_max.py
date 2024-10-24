import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestFunctionsMax(unittest.TestCase):
    def test_function_max1(self):
        print("")
        path = CsvPath()
        Save._save(path, "test_function_max1")
        path.parse(
            f"""
            ${PATH}[*] [
                @the_max = max(#firstname)
                no()
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_max2(self):
        print("")
        path = CsvPath()
        Save._save(path, "test_function_max2")
        path.parse(
            f"""
            ${PATH}[*] [
                @the_max = max(#1)
                no()
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()
