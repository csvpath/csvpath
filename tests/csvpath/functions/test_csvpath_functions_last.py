import unittest
import pytest
import os
from csvpath import CsvPath
from csvpath.matching.matcher import Matcher
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
EMPTY = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}empty.csv"
MAR = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}March-2024.csv"


class TestCsvPathFunctionsLast(unittest.TestCase):
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
            f"""${PATH}[*]
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
