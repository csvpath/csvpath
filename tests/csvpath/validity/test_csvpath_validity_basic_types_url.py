import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.functions.types.url import Url

PATH_1 = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}types.csv"
PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}types2.csv"


class TestCsvPathValidityValidBasicTypesUrl(unittest.TestCase):
    def test_validity_url_0(self):
        assert Url._is_match("http://cricket.com")
        assert Url._is_match("http://play.cricket.com")
        assert Url._is_match("https://play.cricket.net:80/a.html")
        assert not Url._is_match("s3://play.cricket.net:80/a.html")
        assert not Url._is_match("butterfly")
        assert not Url._is_match(None)
        assert not Url._is_match("")

    def test_validity_url_1(self) -> None:
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
                ~  ~
                ${PATH}[1*] [
                    push.distinct("c7", datatype(#url))
                ]"""
        )
        path.fast_forward()
        vs = path.variables
        assert len(vs["c7"]) == 2
        assert "url" in vs["c7"]
        assert "none" in vs["c7"]

    def test_validity_url_2(self) -> None:
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
                ~  ~
                ${PATH_1}[1*] [
                    print("line: $.csvpath.line_number: url: $.headers.url")
                    line( wildcard(), url.distinct(#url), wildcard() )
                ]"""
        )
        #
        # no assertion. doesn't blow up.
        #
        path.fast_forward()

    def test_validity_url_3(self) -> None:
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
                ~ validation-mode:raise, print ~
                ${PATH}[1*] [
                    line( wildcard(7), url.distinct(#7), blank() )
                ]"""
        )
        #
        # no assertion. blows up.
        #
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_validity_url_4(self) -> None:
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
                ~  ~
                ${PATH}[1*] [
                    print("$.csvpath.line_number: $.headers.url")
                    line( wildcard(), url.distinct(#url), wildcard() )
                ]"""
        )
        #
        # no assertion. blows up.
        #
        with pytest.raises(MatchException):
            path.fast_forward()

    def test_validity_url_5(self) -> None:
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
                ~  ~
                ${PATH}[1-3] [
                    print("$.csvpath.line_number: $.headers.url")
                    line( wildcard(), url.distinct(#url), wildcard() )
                ]"""
        )
        #
        # no assertion. doesn't blow up.
        #
        path.fast_forward()
