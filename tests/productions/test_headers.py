import os
import unittest
import pytest
from lark.exceptions import VisitError, UnexpectedCharacters
from csvpath import CsvPath
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.productions import Header

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"
FILE = f"tests{os.sep}test_resources{os.sep}March-2024.csv"


class TestHeaders(unittest.TestCase):
    def test_header_names0(self):
        path = CsvPath()
        path.add_to_config("errors", "csvpath", "raise, collect, print")
        path.OR = True
        path.parse(
            f"""${FILE}[*][
                starts_with(#0, "#") -> @runid.notnone = regex( /Run ID: ([0-9]*)/, #0, 1 )
                starts_with(#0, "#") -> @userid.notnone = regex( /User: ([a-zA-Z0-9]*)/, #0, 1 )

                skip( lt(count_headers_in_line(), 9) )

                @header_change = mismatch("signed")
                gt( @header_change, 9) ->
                      reset_headers(
                        print("\nResetting headers to: $.csvpath.headers"))

                print.onchange.once(
                    "Number of headers changed by $.variables.header_change",
                        print("See line $.csvpath.line_number", skip()))

                not( in( #category, "OFFICE|COMPUTING|FURNITURE|PRINT|FOOD|OTHER" ) ) ->
                    print( "Bad category $.headers.category at line $.csvpath.count_lines ", fail())

                not( exact( end(), /\\$?(\\d*\\.\\d{0, 2})/ ) ) ->
                    print("Bad price $.headers.'a price' at line  $.csvpath.count_lines", fail())

                not( #SKU ) -> print("No SKU at line $.csvpath.count_lines in $.csvpath.headers", fail())
                not( #UPC ) -> print("No UPC at line $.csvpath.count_lines", fail())

            ]"""
        )
        lines = path.collect()
        assert len(lines) == 3

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
        with pytest.raises(VisitError):
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
