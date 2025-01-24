import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = "tests/test_resources/emails.csv"


class TestFunctionsEmail(unittest.TestCase):
    def test_function_email_1(self):
        path = (
            CsvPath()
            .parse(
                f"""${PATH}[1*][
                @v = email( "email" )
                print("email? $.headers.email: $.variables.v")
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
            True,
            True,
            True,
            False,
            False,
            False,
            False,
            False,
            False,
        ]

    def test_function_email_2(self):
        path = CsvPath().parse(
            f"""${PATH}[1*][
                @v2 = email.notnone( none() )
            ]"""
        )
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_email_3(self):
        path = (
            CsvPath()
            .parse(
                f"""${PATH}[1*][
                @v = email( none() )
            ]"""
            )
            .fast_forward()
        )
        assert path.variables["v"] is True
