import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.functions.types.decimal import Decimal
from csvpath.matching.functions.types.boolean import Boolean
from csvpath.matching.functions.types.datef import Date
from csvpath.matching.functions.types.string import String
from csvpath.matching.functions.types.nonef import Nonef
from csvpath.matching.functions.types.email import Email
from csvpath.matching.functions.types.url import Url

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}types.csv"


class TestCsvPathValidityRecognizeBasicTypes(unittest.TestCase):
    def test_validity_is_match_classes_int(self):
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

    def test_validity_is_match_classes_dec(self):
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

    def test_validity_is_match_classes_bool(self):
        assert not Boolean._is_match("1", strict=True)[0]
        assert not Boolean._is_match(None, strict=True)[0]
        assert not Boolean._is_match("no", strict=True)[0]
        assert not Boolean._is_match("yes", strict=True)[0]
        assert Boolean._is_match("true")[0]
        assert Boolean._is_match("True")[0]
        assert Boolean._is_match(True)[0]
        assert Boolean._is_match("false")[0]

    def test_validity_is_match_classes_date(self):
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

    def test_validity_is_match_classes_str(self):
        assert not String._is_match("")
        assert String._is_match("astring")
        assert String._is_match("5")
        assert not String._is_match(5)
        assert not String._is_match(None)

    def test_validity_is_match_classes_none(self):
        assert Nonef._is_match(None)
        assert Nonef._is_match("None")
        assert Nonef._is_match("NONE")
        assert Nonef._is_match("nan")
        assert Nonef._is_match("")
        assert not Nonef._is_match("a")
        assert not Nonef._is_match(0)
        assert not Nonef._is_match(False)

    def test_validity_is_match_classes_email(self):
        assert Email._is_match("a@bird.com")
        assert Email._is_match("a.a@b.com")
        assert Email._is_match("a.a@c.b.com")
        assert Email._is_match("a.a@c.b.io")
        assert Email._is_match("ABC@deF.com")
        assert not Email._is_match("a@.com")
        assert not Email._is_match("a@.")
        assert not Email._is_match("a@.")
        assert not Email._is_match("@cat")

    def test_validity_is_match_classes_url(self):
        assert Url._is_match("http://cricket.com")
        assert Url._is_match("http://play.cricket.com")
        assert Url._is_match("https://play.cricket.net:80/a.html")
        assert not Url._is_match("s3://play.cricket.net:80/a.html")
        assert not Url._is_match("butterfly")
        assert not Url._is_match(None)
        assert not Url._is_match("")

    def test_validity_recognize_datatype(self) -> None:
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        path.parse(
            f"""
                ~  ~
                ${PATH}[1*] [
                    push.distinct("c0", datatype(#decimal))
                    push.distinct("c1", datatype(#integer))
                    push.distinct("c2", datatype(#boolean))
                    push.distinct("c3", datatype(#date))
                    push.distinct("c4", datatype(#datetime))
                    push.distinct("c5", datatype(#none))
                    push.distinct("c6", datatype(#email))
                    push.distinct("c7", datatype(#url))
                    push.distinct("c8", datatype(#string))
                ]"""
        )
        path.fast_forward()
        vs = path.variables
        print(f"vs: {vs}")
        assert "c0" in vs
        assert "c1" in vs
        assert "c2" in vs
        assert "c3" in vs
        assert "c4" in vs
        assert "c5" in vs
        assert "c6" in vs
        assert "c7" in vs
        assert "c8" in vs

        assert len(vs["c0"]) == 2
        assert "decimal" in vs["c0"]
        assert "integer" in vs["c0"]

        assert len(vs["c1"]) == 2
        assert "decimal" in vs["c1"]
        assert "integer" in vs["c1"]

        assert len(vs["c2"]) == 1
        assert vs["c2"][0] == "boolean"

        assert len(vs["c3"]) == 1
        assert vs["c3"][0] == "date"

        assert len(vs["c4"]) == 2
        assert "datetime" in vs["c4"]
        assert "date" in vs["c4"]

        assert len(vs["c5"]) == 1
        assert vs["c5"][0] == "none"

        assert len(vs["c6"]) == 1
        assert vs["c6"][0] == "email"

        assert len(vs["c7"]) == 2
        assert "url" in vs["c7"]
        assert "none" in vs["c7"]

        assert len(vs["c8"]) == 1
        assert vs["c8"][0] == "string"
