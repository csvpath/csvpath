import os
import unittest
import pytest
from lark.exceptions import VisitError, UnexpectedCharacters
from csvpath import CsvPath
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.util.exceptions import ChildrenException
from csvpath.matching.productions import Header

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
FILE = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}March-2024.csv"


class TestCsvPathProductionsHeaders(unittest.TestCase):
    def test_header_names0(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.OR = True
        path.parse(
            f"""
                ~ validation-mode:no-raise, no-stop, print, no-fail, collect ~
                ${FILE}[*][
                starts_with(#0, "#") -> @runid.notnone = regex( /Run ID: ([0-9]*)/, #0, 1 )
                starts_with(#0, "#") -> @userid.notnone = regex( /User: ([a-zA-Z0-9]*)/, #0, 1 )

                skip( lt(count_headers_in_line(), 9) )

                @header_change = mismatch("signed")
                gt( @header_change, 9) ->
                      reset_headers(
                        print("\nResetting headers to: $.csvpath.headers"))

                print.onchange.once(
                    "Number of headers changed by $.variables.header_change",
                        print("See line $.csvpath.line_number
                        ", skip()))

                ~
                    we create two vars and two header existance tests. each of these 4
                    determins match because we are OR -- match takes just one positive.
                    They are also used to print errors. in this case, we want the error
                    report as our main validation. the matched lines only indicate there
                    is some valid data per line, not that the line is fully valid. this
                    is a very particular validation strategy. If we wanted to do it with
                    AND we would just use .nocontrib on the left hand sides. i.e. both
                    are pretty easy, just a bit different.
                ~

                ~ 1x wrong, 2nd item ~
                @in = in( #category, "OFFICE|COMPUTING|FURNITURE|PRINT|FOOD|OTHER" )
                not( @in.asbool ) ->
                    error.category( "Bad category $.headers.category at line $.csvpath.count_lines ")

                ~ 2x wrong, 2nd and 3rd items ~
                @price = exact( end(), /\\$?\\d*\\.\\d{{2}}/ )
                not( @price.asbool ) ->
                    error.price("Bad price $.headers.'a price' at line  $.csvpath.count_lines", fail())

                ~ 1x missing, 1st item ~
                #SKU
                not( #SKU ) ->
                    error.sku("No SKU at line $.csvpath.count_lines in $.csvpath.headers", fail())

                ~ always exists ~
                #UPC
                not( #UPC ) ->
                    error.upc("No UPC at line $.csvpath.count_lines", fail())
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 3
        assert path.errors_count == 4

    def test_header_names11(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(f"""${PATH}[*][ #"a.b" ]""")
        # the parser removes the '#' before instantiating the header
        h = Header(None, value="fruitbat", name='"a.b"')
        assert h.name == "a.b"
        h = Header(None, value="fruitbat", name='"a.b".c')
        assert h.name == "a.b"
        assert h.first_non_term_qualifier() == "c"

    def test_header_names1(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(
            f"""${PATH}[*][
                #a
                #b.asbool
                #b.asbool.onchange
                #c_is_my_name
            ]"""
        )
        path.fast_forward()

    def test_header_names2(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(
            f"""${PATH}[*][
                #_hmm
                #123me
                #3.3
                #Iam_capped
                #-dashed
                #also-dashed
                #includes@sign.com
            ]"""
        )
        path.fast_forward()

    def test_header_names3(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(f"""${PATH}[*][#no-spaces #"I have spaces" #nothing ]""")
        path.fast_forward()

    def test_header_bad_names1(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(f"""${PATH}[*][ #.hidden ]""")
        path.config.add_to_config("errors", "csvpath", "raise")
        # with pytest.raises(VisitError):
        with pytest.raises(ChildrenException):
            path.fast_forward()  # pragma: no cover

    def test_header_bad_names2(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(f"""${PATH}[*][#!not allowed]""")
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(UnexpectedCharacters):
            path.fast_forward()  # pragma: no cover

    def test_header_bad_names3(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(
            f"""
                   ${PATH}[*][
                   #'not allowed'
                ]"""
        )
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(UnexpectedCharacters):
            path.fast_forward()  # pragma: no cover

    def test_header_bad_names4(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.parse(f"""${PATH}[*][ #$$ ]""")
        path.config.add_to_config("errors", "csvpath", "raise")
        with pytest.raises(UnexpectedCharacters):
            path.fast_forward()  # pragma: no cover

    def test_header_bad_names5(self):
        path = CsvPath().parse(f"""${PATH}[*][ #`no good` ]""")
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        with pytest.raises(UnexpectedCharacters):
            path.fast_forward()  # pragma: no cover


NUMERIC_LIKE = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}numeric_like_headers.csv"
DASH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}dash_headers.csv"


def _header_value(header: str, *, file: str = None):
    # numeric_like_headers.csv: a,-1,1.5,1_0,b / A,NEG,DECIMAL,UNDERSCORE,LAST
    path = CsvPath()
    path.parse(f"""${file or NUMERIC_LIKE}[1][ @v = {header} ]""")
    path.fast_forward()
    return path.variables.get("v")


class TestCsvPathProductionsNumericLikeHeaderNames(unittest.TestCase):
    """A header name with a decimal point or digit underscores is a name.
    Before, "1.5" and "1.0" were column 1 and "1_0" was column 10. A decimal
    is a 0-based position (docs/headers.md). A negative integer is still a
    position from the end, as before, until we decide if it should be a
    name (#607); these tests pin that, so a change to it is deliberate."""

    def test_decimal_looking_name_is_a_name(self):
        assert _header_value('#"1.5"') == "DECIMAL"

    def test_whole_float_looking_name_is_a_name(self):
        # numeric_like_headers.csv has no "1.0" header
        assert _header_value('#"1.0"') is None

    def test_negative_integer_is_still_a_position_from_the_end(self):
        assert _header_value('#"-1"') == "LAST"
        assert _header_value("#-1") == "LAST"
        assert _header_value('#" -1 "') == "LAST"
        assert _header_value('#"-2"') == "UNDERSCORE"
        assert _header_value('#"-0"') == "A"

    def test_underscore_digits_name_is_a_name(self):
        assert _header_value("#1_0") == "UNDERSCORE"

    def test_only_one_leading_minus_makes_a_position(self):
        # dash_headers.csv: --1,x / DASHDASH,X
        assert _header_value("#--1", file=DASH) == "DASHDASH"

    def test_decimal_is_still_a_position(self):
        assert _header_value("#1") == "NEG"
        assert _header_value('#"4"') == "LAST"

    def test_padded_decimal_is_still_a_position(self):
        assert _header_value('#" 2 "') == "DECIMAL"

    def test_names_are_looked_up_exactly(self):
        assert _header_value("#b") == "LAST"
        assert _header_value('#" b "') is None
        assert _header_value("#nope") is None

    def test_position_past_the_end_is_none(self):
        assert _header_value('#"9"') is None
