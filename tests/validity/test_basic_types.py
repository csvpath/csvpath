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


class TestValidBasicTypes(unittest.TestCase):
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

    def test_validity_boolean1(self):
        path = CsvPath()
        Save._save(path, "test_validity_boolean1")
        path.parse(
            f""" ${PATH}[*][
                boolean(yes())
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_boolean2(self):
        path = CsvPath()
        Save._save(path, "test_validity_boolean2")
        path.parse(
            f""" ~ None is acceptable if not notnone but it is not
                   a boolean value so we get nothing here ~
            ${PATH}[*][
                boolean(none())
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_validity_boolean3(self):
        path = CsvPath()
        Save._save(path, "test_validity_boolean3")
        path.parse(
            f""" ~ 1 is the 2nd column. it doesn't have booleans.
                   validation-mode: no-raise, no-stop
                 ~
            ${PATH}[*][
                boolean("1")
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_validity_boolean4(self):
        path = CsvPath()
        Save._save(path, "test_validity_boolean4")
        path.parse(
            f""" ~ -1 is not a boolean and is not convertable to a boolean ~
            ${PATH}[*][
                boolean(-1)
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_boolean45(self):
        path = CsvPath()
        Save._save(path, "test_validity_boolean45")
        path.parse(
            f""" ${PATH}[*][
                boolean(5)
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_boolean5(self):
        path = CsvPath()
        Save._save(path, "test_validity_boolean5")
        path.parse(
            f""" ${PATH}[*][
                boolean("fish")
            ]"""
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_validity_boolean6(self):
        path = CsvPath()
        Save._save(path, "test_validity_boolean6")
        path.parse(
            f""" ~ note that @b standing alone is an existance test.
                   that means it's not yes()'s boolean or the boolean()'s
                   validation that yes() is a boolean. it is the
                   existance of a value @b. ~
            ${PATH}[*][
                @b = boolean(yes())
                @b
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_validity_boolean7(self):
        path = CsvPath()
        Save._save(path, "test_validity_boolean7")
        path.parse(
            f""" ${PATH}[*][
                ~ yes, it's a bool ~
                @b = boolean(no())
                ~ yes, it exists ~
                @b
                ~ no, it is not True ~
                @b.asbool
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_validity_boolean8(self):
        path = CsvPath()
        Save._save(path, "test_validity_boolean8")
        path.parse(
            f""" ${PATH}[*][
                @b.asbool = boolean(false())
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0
