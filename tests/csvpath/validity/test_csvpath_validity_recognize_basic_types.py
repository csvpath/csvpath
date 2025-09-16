import unittest
import pytest
import os
from csvpath.matching.functions.types.decimal import Decimal
from csvpath.matching.functions.types.boolean import Boolean
from csvpath.matching.functions.types.datef import Date
from csvpath.matching.functions.types.string import String
from csvpath.matching.functions.types.nonef import Nonef
from csvpath.matching.functions.types.email import Email
from csvpath.matching.functions.types.url import Url


class TestCsvPathValidityRecognizeBasicTypes(unittest.TestCase):
    def test_is_match_classes_int(self):
        assert Decimal._is_match(
            name="integer", value="25", dmax=50, dmin=0, strict=True
        )[0]
        assert not Decimal._is_match(
            name="integer", value="25.5", dmax=50, dmin=0, strict=True
        )[0]
        assert not Decimal._is_match(
            name="integer", value="25.0", dmax=50, dmin=0, strict=True
        )[0]
        assert Decimal._is_match(
            name="integer", value="25.0", dmax=50, dmin=0, strict=False
        )[0]
        assert not Decimal._is_match(
            name="integer", value="fish", dmax=50, dmin=0, strict=True
        )[0]
        assert not Decimal._is_match(
            name="integer", value="-1", dmax=50, dmin=0, strict=True
        )[0]

    def test_is_match_classes_dec(self):
        assert not Decimal._is_match(
            name="decimal", value="25", dmax=50, dmin=0, strict=True
        )[0]
        assert Decimal._is_match(
            name="decimal", value="25.5", dmax=50, dmin=0, strict=True
        )[0]
        assert Decimal._is_match(
            name="decimal", value="25.0", dmax=50, dmin=0, strict=True
        )[0]
        assert Decimal._is_match(
            name="decimal", value="25", dmax=50, dmin=0, strict=False
        )[0]
        assert not Decimal._is_match(
            name="decimal", value="fish", dmax=50, dmin=0, strict=True
        )[0]
        assert not Decimal._is_match(
            name="decimal", value="-.1", dmax=-1, dmin=-5, strict=True
        )[0]

    def test_is_match_classes_bool(self):
        assert not Boolean._is_match("1")[0]
        assert not Boolean._is_match(None)[0]
        assert not Boolean._is_match("no")[0]
        assert not Boolean._is_match("yes")[0]
        assert Boolean._is_match("true")[0]
        assert Boolean._is_match("True")[0]
        assert Boolean._is_match(True)[0]
        assert Boolean._is_match("false")[0]

    def test_is_match_classes_date(self):
        assert not Date._is_match(
            is_datetime=True, value=""
        )  # the function returns true unless .notnone, but this doesn't
        assert Date._is_match(is_datetime=True, value="2025/01/01 00:01:01")
        assert not Date._is_match(is_datetime=True, value="2025/01/01", strict=True)
        assert Date._is_match(is_datetime=True, value="2025/01/01", strict=False)
        assert not Date._is_match(
            is_datetime=False, value="2025/01/01 01:01:01", strict=True
        )
        assert Date._is_match(is_datetime=False, value="2025/01/01", strict=True)
        assert Date._is_match(is_datetime=False, value="2025/01/01", strict=False)

    def test_is_match_classes_str(self):
        assert not String._is_match("")
        assert String._is_match("astring")
        assert String._is_match("5")
        assert not String._is_match(5)
        assert not String._is_match(None)

    def test_is_match_classes_none(self):
        assert Nonef._is_match(None)
        assert Nonef._is_match("None")
        assert Nonef._is_match("NONE")
        assert Nonef._is_match("nan")
        assert Nonef._is_match("")
        assert not Nonef._is_match("a")
        assert not Nonef._is_match(0)
        assert not Nonef._is_match(False)

    def test_is_match_classes_email(self):
        assert Email._is_match("a@bird.com")
        assert Email._is_match("a.a@b.com")
        assert Email._is_match("a.a@c.b.com")
        assert Email._is_match("a.a@c.b.io")
        assert Email._is_match("ABC@deF.com")
        assert not Email._is_match("a@.com")
        assert not Email._is_match("a@.")
        assert not Email._is_match("a@.")
        assert not Email._is_match("@cat")

    def test_is_match_classes_url(self):
        assert Url._is_match("http://cricket.com")
        assert Url._is_match("http://play.cricket.com")
        assert Url._is_match("https://play.cricket.net:80/a.html")
        assert not Url._is_match("s3://play.cricket.net:80/a.html")
        assert not Url._is_match("butterfly")
        assert not Url._is_match(None)
        assert not Url._is_match("")
