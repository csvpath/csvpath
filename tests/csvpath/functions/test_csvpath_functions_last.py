import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.matcher import Matcher
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
EMPTY = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}empty.csv"
MAR = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}March-2024.csv"
LAST = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}last_blank.csv"


class TestCsvPathFunctionsLast(unittest.TestCase):
    def test_function_last_blank_1(self):
        path = CsvPath().fast_forward(
            f"""
        ~ eval last() on last line even though blank ~
            ${LAST}[*][
                @x = #name
                last() -> @y = #name
            ]
        """
        )
        print(f"path.variables: {path.variables}")
        x = path.variables["x"]
        y = path.variables["y"]
        #
        # we scan all lines. we would skip the last for being
        # blank, but we don't skip because last(). however,
        # y finds None, as you would expect.
        #
        assert y is None
        assert x != y

    def test_function_last_blank_2a(self):
        path = CsvPath().parse(
            f"""
        ~ eval last() on last scanned line ~
            ${LAST}[0-1][
                print("line: $.csvpath.line_number")
                @x = last(put("y", line_number()))
            ]
        """
        )
        for i, _ in enumerate(path.next()):
            print(f"path.variables: [{i}]{path.variables}, _: {_}")
        assert 1 == path.variables["y"]
        x = path.variables["x"]
        #
        # WARNING: at this time the result in @x is False. ideally it should be
        # True, and atm, last() does return True, and would assign True but for
        # the inner function of last(). because of the inner function x is False.
        # craziness, but after looking at it multiple times over months, not
        # amenable to a fix without major refactor--or brain upgrade. in a perfect
        # world we'd do it. but under the circumstances it is not practical to
        # refactor for a relatively infrequent, if not rare, corner case. if we
        # do refactor it will probably be in the context of a v2 language version
        # after at least moderate success and deploy-learnings.
        #
        assert x is False

    def test_function_last_blank_2b(self):
        path = CsvPath().parse(
            f"""
        ~ eval last() on last scanned line ~
            ${LAST}[0-1][
                print("line: $.csvpath.line_number")
                last(put("y", line_number()))
            ]
        """
        )
        for i, _ in enumerate(path.next()):
            print(f"path.variables: [{i}]{path.variables}, _: {_}")
        assert 1 == path.variables["y"]

    def test_function_last_blank_2c(self):
        path = CsvPath().parse(
            f"""
        ~ eval last() on last scanned line ~
            ${LAST}[0-1][
                print("line: $.csvpath.line_number")
                @x = last()
            ]
        """
        )
        for i, _ in enumerate(path.next()):
            print(f"path.variables: [{i}]{path.variables}, _: {_}")
        assert True is path.variables["x"]

    def test_function_last_blank_3(self):
        path = CsvPath().parse(
            f"""
        ~ eval last() on last line and skip ~
            ${LAST}[0-2][
                yes() -> last(skip())
                @x = line_number()
            ]
        """
        )
        for i, _ in enumerate(path.next()):
            print(f"path.variables: [{i}]{path.variables}")
        x = path.variables["x"]
        assert x == 1

    def test_function_last_blank_4(self):
        path = CsvPath().parse(
            f"""
        ~ eval last() on last line and skip ~
            ${LAST}[0-2][
                yes() -> last(
                            and(
                                put("y", "ha"),
                                skip()
                            )
                        )
                @x = line_number()
            ]
        """
        )
        for i, _ in enumerate(path.next()):
            print(f"path.variables: [{i}]{path.variables}")
        x = path.variables["x"]
        assert x == 1

    def test_function_last_blank_5(self):
        path = CsvPath().parse(
            f"""
        ~ eval last() on last line and skip ~
            ${LAST}[0-3][
                yes() -> last(
                                put("x", empty(headers()) )
                            )
                @x = line_number()
            ]
        """
        )
        for i, _ in enumerate(path.next()):
            print(f"path.variables: [{i}]{path.variables}")
        x = path.variables["x"]
        assert x is True

    def test_function_last1(self):
        csvpath = f"""${MAR}[*][
            ~ Capture metadata from comments ~
                skip( lt(count_headers_in_line(), 9) )
                @header_change = mismatch("signed")
                gt( @header_change, 9) -> reset_headers(print("Resetting headers"))
                print.onchange.once("headers changed", skip())
                ~
                below(total_lines(), 10)
                ~
                last.onmatch() ->
                      push("lastish", line_number())

          ]"""
        path = CsvPath()
        path.OR = True
        path.parse(csvpath)
        path.collect()
        assert len(path.variables["lastish"]) == 1

    # FIXME: this is not really a deterministic test.
    def test_function_last3(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*] [ yes() -> print("$.csvpath.line_count")
                last() -> print("the last row is $.csvpath.line_count")
            ]
            """
        )
        path.fast_forward()

    def test_function_last4(self):
        path = CsvPath()
        path.config.csvpath_errors_policy = ["raise", "print"]
        path.parse(
            f"""~ validation-mode:collect, raise ~ ${PATH}[*]
                            [
                            ~ the point of this test is that: tally works even when no()
                              and that manually replacing a tally var with a string blows up because
                              it needs to be a number. hmmm and ohhh are a sideshow. ~
                                no()
                                tally(#lastname)
                                @hmmm = @lastname.Bat
                                @ohhh = @hmmm.fish
                                @tally_lastname.Bat = "fred"
                            ]
                   """
        )
        with pytest.raises(MatchException):
            path.collect()

    def test_function_last5(self):
        # must run last even though line is blank
        path = CsvPath()
        path.parse(
            f"""${EMPTY}[*][
                   last(print("last!"))
            ] """
        )
        path.fast_forward()
        assert path.printers[0].last_line == "last!"
        path = CsvPath()
        path.parse(
            f"""${EMPTY}[*][
                   last() -> print("last!")
            ] """
        )
        path.fast_forward()
        assert path.printers[0].last_line == "last!"
