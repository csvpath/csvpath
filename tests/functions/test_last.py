import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.matcher import Matcher
from csvpath.matching.util.exceptions import MatchException

PATH = "tests/test_resources/test.csv"
EMPTY = "tests/test_resources/empty2.csv"


class TestFunctionsLast(unittest.TestCase):
    def test_function_last1(self):
        csvpath = """$tests/test_resources/March-2024.csv[*][
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
        path.config.csvpath_errors_policy = ["raise"]
        path.parse(
            f"""${PATH}[*]
                            [
                                tally(#lastname) no()
                                @hmmm = @lastname.Bat
                                @ohhh = @hmmm.fish
                                @tally_lastname.Bat = "fred"
                            ]
                   """
        )
        with pytest.raises(MatchException):
            path.collect()
            assert path.variables["tally_lastname"]["Bat"] == "fred"
            assert path.variables["hmmm"] == 7
            assert path.variables["ohhh"] is None

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
