import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.util.config import Config
from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.util.exceptions import ChildrenException
from tests.save import Save

PATH = "tests/test_resources/test.csv"
NUMBERS = "tests/test_resources/numbers3.csv"


class TestValidBasicTypesDate(unittest.TestCase):
    def test_validity_date1(self):
        path = CsvPath()
        Save._save(path, "test_validity_date1")
        path.parse(
            f"""~id:validity_date1~ ${PATH}[*][
                date()
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_validity_date2(self):
        path = CsvPath()
        Save._save(path, "test_validity_date2")
        path.parse(
            f"""~id:validity_date2~ ${PATH}[*][
                date.notnone(none())
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_validity_date3(self):
        path = CsvPath()
        Save._save(path, "test_validity_date3")
        path.parse(
            f"""~id:validity_date3~ ${PATH}[*][
                date("2024-01-01")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_date4(self):
        path = CsvPath()
        Save._save(path, "test_validity_date4")
        path.parse(
            f"""~id:validity_date4~ ${PATH}[*][
                @d = date("2024-01-01")
                date(@d)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_date5(self):
        path = CsvPath()
        Save._save(path, "test_validity_date5")
        path.parse(
            f"""~id:validity_date5~ ${PATH}[*][
                date("the 3rd of feb")
            ]"""
        )
        with pytest.raises(MatchException):
            lines = path.collect()
            assert len(lines) == 0

    def test_validity_date6(self):
        path = CsvPath()
        Save._save(path, "test_validity_date6")
        path.parse(
            f"""~id:validity_date6~ ${PATH}[*][
                date("the 3rd of feb", "%Y")
            ]"""
        )
        with pytest.raises(MatchException):
            lines = path.collect()
            assert len(lines) == 0

    def test_validity_now1(self):
        path = CsvPath()
        Save._save(path, "test_validity_now2")
        path.parse(
            f"""~id:validity_now1~ ${PATH}[*][
                now("%Y")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_now2(self):
        path = CsvPath()
        Save._save(path, "test_validity_now2")
        path.parse(
            f"""~id:validity_now2~ ${PATH}[*][
                today("%Y")
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()
            # assert len(lines) == 0

    def test_validity_now3(self):
        path = CsvPath()
        Save._save(path, "test_validity_now3")
        path.parse(
            f"""~id:validity_now3~ ${PATH}[*][
                now()
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_now4(self):
        path = CsvPath()
        Save._save(path, "test_validity_now4")
        path.parse(
            f"""~id:validity_now4~ ${PATH}[*][
                now("2024-01-01","%Y")
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()
