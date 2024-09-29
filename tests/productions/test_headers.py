import unittest
import pytest
from lark.exceptions import VisitError, UnexpectedCharacters
from csvpath.csvpath import CsvPath
from csvpath.matching.util.exceptions import ChildrenException
from csvpath.matching.util.expression_utility import ExpressionUtility
from tests.save import Save

PATH = "tests/test_resources/test.csv"


class TestHeaders(unittest.TestCase):
    def test_header_names0(self):
        print("")
        path = CsvPath()
        path.OR = True
        Save._save(path, "test_header_names0")
        path.parse(
            """$tests/test_resources/March-2024.csv[*][
                starts_with(#0, "#") -> @runid.notnone = regex( /Run ID: ([0-9]*)/, #0, 1 )
                starts_with(#0, "#") -> @userid.notnone = regex( /User: ([a-zA-Z0-9]*)/, #0, 1 )

                skip( lt(count_headers_in_line(), 9) )

                @header_change = mismatch("signed")
                gt( @header_change, 9) ->
                      reset_headers(
                        print("\nResetting headers to: $.csvpath.headers"))

                print.onchange.once(
                    "\nNumber of headers changed by $.variables.header_change",
                        print("See line $.csvpath.line_number", skip()))

                not( in( #category, "OFFICE|COMPUTING|FURNITURE|PRINT|FOOD|OTHER" ) ) ->
                    print( "\nBad category $.headers.category at line $.csvpath.count_lines ", fail())


                not( exact( end(), /\\$?(\\d*\\.\\d{0,2})/ ) ) ->
                    print("\nBad price $.headers.'a price' at line  $.csvpath.count_lines", fail())

                not( #SKU ) -> print("\nNo SKU at line $.csvpath.count_lines in $.csvpath.headers", fail())
                not( #UPC ) -> print("\nNo UPC at line $.csvpath.count_lines", fail())

            ]"""
        )
        lines = path.collect()
        print("")
        print(f"test_header_names0: lines: {lines}\n")
        print("")
        print(f"test_header_names0: lines cnt: {len(lines)}\n")
        print("")
        print(f"test_header_names0: vars: {path.variables}")
        print("")
        """
        for s in path.variables["votes"]:
            print(f">>> {s}")
        for s in path.variables["dowhens"]:
            print(f">>> {s}")
        """

        assert len(lines) == 3

    def test_header_names1(self):
        path = CsvPath()
        Save._save(path, "test_header_names")
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
        Save._save(path, "test_header_names")
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
        Save._save(path, "test_header_names")
        path.parse(
            f"""${PATH}[*][
                #no-spaces
                #"I have spaces"
                #nothing
            ]"""
        )
        path.fast_forward()

    def test_header_bad_names1(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["raise"]
        with pytest.raises(VisitError):
            path.parse(
                f"""${PATH}[*][
                    #.hidden
                ]"""
            )
            path.fast_forward()  # pragma: no cover

    def test_header_bad_names2(self):
        path = CsvPath()
        with pytest.raises(UnexpectedCharacters):
            path.parse(
                f"""${PATH}[*][
                    #!not allowed
                ]"""
            )
            path.fast_forward()  # pragma: no cover

    def test_header_bad_names3(self):
        path = CsvPath()
        with pytest.raises(UnexpectedCharacters):
            path.parse(
                f"""${PATH}[*][
                    #'not allowed'
                ]"""
            )
            path.fast_forward()  # pragma: no cover
        print("test_header_bad_names: done")

    def test_header_bad_names4(self):
        path = CsvPath()
        with pytest.raises(UnexpectedCharacters):
            path.parse(
                f"""${PATH}[*][
                    #$$
                ]"""
            )
            path.fast_forward()  # pragma: no cover

    def test_header_bad_names5(self):
        path = CsvPath()
        with pytest.raises(UnexpectedCharacters):
            path.parse(
                f"""${PATH}[*][
                    #`no good`
                ]"""
            )
            path.fast_forward()  # pragma: no cover
