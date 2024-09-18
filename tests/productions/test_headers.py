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
                ~
                line_number() == 9 -> debug()
                line_number() == 11 -> debug("info")
                ~
                skip( lt(count_headers_in_line(), 9) )
                @header_change = mismatch("signed")

                gt( @header_change, 9) -> reset_headers(skip())

                not(#SKU)

                push("votes", vote_stack())

            ]"""
        )
        lines = path.collect()
        print(f"test_header_names0: lines: {lines}\n")
        print(f"test_header_names0: lines cnt: {len(lines)}\n")
        print(f"test_header_names0: vars: {path.variables}")

        for s in path.variables["votes"]:
            print(f">>> {s}")
        assert len(lines) == 1

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
