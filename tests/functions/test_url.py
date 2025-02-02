import os
import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

URLS = f"tests{os.sep}test_resources{os.sep}urls.csv"


class TestFunctionsUrl(unittest.TestCase):
    def test_function_url_1(self):
        path = (
            CsvPath()
            .parse(
                f"""${URLS}[1*][
                @v = url( #url )
                push( "u", @v )
            ]"""
            )
            .fast_forward()
        )
        u = path.variables["u"]
        assert u[0:3] == [True, True, True]
        assert u[3:7] == [False, False, False, False]
        assert u[7] is True
        assert u[8:11] == [False, False, False]
        assert u[11] is True

    def test_function_url_2(self):
        path = (
            CsvPath()
            .parse(f"""${URLS}[13*][ @v = url( #url ) push( "u", @v ) ]""")
            .fast_forward()
        )
        u = path.variables["u"]
        assert u[0:3] == [False, False, False]

    def test_function_url_3(self):
        path = CsvPath().parse(
            f"""${URLS}[1*][
                @v2 = url.notnone( none() )
            ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_function_url_4(self):
        path = CsvPath().parse(f"""${URLS}[1*][ @v = url( none() ) ]""").fast_forward()
        assert path.variables["v"] is False
