import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException
from csvpath.matching.functions.types.email import Email

PATH1 = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}types.csv"
PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}types2.csv"


class TestCsvPathValidityValidBasicTypesEmail(unittest.TestCase):
    def test_validity_email_1(self):
        assert Email._is_match("a@bird.com")
        assert Email._is_match("a.a@b.com")
        assert Email._is_match("a.a@c.b.com")
        assert Email._is_match("a.a@c.b.io")
        assert Email._is_match("ABC@deF.com")
        assert not Email._is_match("a@.com")
        assert not Email._is_match("a@.")
        assert not Email._is_match("a@.")
        assert not Email._is_match("@cat")

    def test_validity_email_2(self) -> None:
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
                ~  ~
                ${PATH1}[1*] [
                    print("email[$.csvpath.line_number]: $.headers.email")
                    push.distinct("c6", datatype(#email))
                ]"""
        )
        path.fast_forward()
        vs = path.variables
        print(f"vs: {vs}")
        assert "c6" in vs
        assert len(vs["c6"]) == 1
        assert vs["c6"][0] == "email"

    def test_validity_email_4(self) -> None:
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
                ~ validation-mode:raise, print ~
                ${PATH}[1*] [
                    line( wildcard(), email.distinct(#email), wildcard() )
                ]"""
        )
        #
        # no assertion. blows up.
        #
        with pytest.raises(MatchException):
            path.fast_forward()
