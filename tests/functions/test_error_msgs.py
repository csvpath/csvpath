import unittest
import os
from csvpath import CsvPath
from csvpath.matching.matcher import Matcher
from csvpath.matching.functions.boolean.any import Any
from csvpath.matching.productions import Expression

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"


class TestFunctionsErrorMsgs(unittest.TestCase):
    def test_function_error_msgs_1(self):
        #
        # this test is just for manual testing. running with
        # all the automated units doesn't hurt.
        #
        print("\n")
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "print")
        path.parse(
            f""" ${PATH}[3][
            print("
Checking file line $.csvpath.line_number")
            print("
int: 1")
                int(#firstname, "five")
            print("
* int: 2")
                @a = int(1.2)
            print("
decimal: 3")
                decimal.strict("5")
            print("
int: 4")
                int.notnone(none())
            print("
int: 5")
                int(1,2,3,4,5)
            print("
* wildcard standing alone: 6")
                wildcard("five")
            print("
date: 7")
                date("2004-01-02", "abcdefg")
            print("
date: 8")
                date("abcdefg", "yyyy-MM-dd")
            print("
line with 2 dates: 9")
                line(
                    date(),
                    date()
                )
            print("
* wildcard with now within line: 10")
                line(
                    wildcard(now())
                )
            print("
* line with 2 ints and a counter: 11")
                line(
                    int(),
                    int(),
                    counter.flies()
                )

        ] """
        )
        path.collect()
        vars = path.variables
        print(f"\nvars: {vars}")
