import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

EMAIL1 = f"tests{os.sep}test_resources{os.sep}emails1.csv"
EMAIL2 = f"tests{os.sep}test_resources{os.sep}emails2.csv"
EMAIL3 = f"tests{os.sep}test_resources{os.sep}emails3.csv"


class TestFunctionsEmail(unittest.TestCase):
    def test_function_email_1(self):
        path = (
            CsvPath()
            .parse(
                f"""${EMAIL1}[1*][
                @v = email( #email )
                push( "e", @v )
            ]"""
            )
            .fast_forward()
        )
        assert path.variables["e"] == [
            True,
            True,
            True,
            True,
        ]

    def test_function_email_2(self):
        path = (
            CsvPath()
            .parse(
                f"""${EMAIL2}[1*][
                @v = email( #email )
                push( "e", @v )
            ]"""
            )
            .fast_forward()
        )
        assert path.variables["e"] == [True, True, True, False, False]

    def test_function_email_3(self):
        path = (
            CsvPath()
            .parse(
                f"""${EMAIL3}[1*][
                @v = email( #email )
                push( "e", @v )
            ]"""
            )
            .fast_forward()
        )
        assert path.variables["e"] == [False, False, False, False]

    def test_function_email_4(self):
        path = CsvPath().parse(f"""${EMAIL1}[1*][ @v2 = email.notnone( none() ) ]""")
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_email_5(self):
        path = (
            CsvPath()
            .parse(
                f"""${EMAIL1}[1*][
                @v = email( none() )
            ]"""
            )
            .fast_forward()
        )
        assert path.variables["v"] is True
