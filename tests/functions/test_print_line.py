import unittest
import pytest
from csvpath import CsvPath
from csvpath.matching.matcher import Matcher

PATH = "tests/test_resources/test.csv"


class TestFunctionsPrintLine(unittest.TestCase):
    def test_function_print_line1(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*][
                   last() -> print_line()
            ] """
        )
        path.fast_forward()
        assert path.printers[0].last_line == "Frog,Bat,growl"

    def test_function_print_line2(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*][
                   last() -> print_line("|","quotes")
            ] """
        )
        path.fast_forward()
        assert path.printers[0].last_line == '"Frog"|"Bat"|"growl"'

    def test_function_print_queue(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*][
                    print("$.csvpath.line_number")
                    print_queue() == 5 -> stop()
            ] """
        )
        path.fast_forward()
        assert path.printers[0].last_line == "4"
